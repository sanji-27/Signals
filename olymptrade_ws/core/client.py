# core/client.py
import asyncio
import logging
import time
from typing import Any, Dict, Optional, Callable, Awaitable, List, Coroutine
from collections import defaultdict
from olymptrade_ws.olympconfig import parameters
from .connection import Connection
from .protocol import format_message, parse_message, generate_uuid
from olymptrade_ws.api import balance, market, trade
import olymptrade_ws.olympconfig.parameters as settings

logger = logging.getLogger(__name__)

class OlympTradeClient:
    def __init__(self, access_token: str, uri: str = parameters.DEFAULT_WEBSOCKET_URI, log_raw_messages: bool = False, account_id: int = None, account_group: str = None):
        logger.info(f"Initializing OlympTradeClient with uri={uri}, log_raw_messages={log_raw_messages}, account_id={account_id}, account_group={account_group}")
        self.access_token = access_token
        self.uri = uri
        self.initial_account_id = account_id
        self.initial_account_group = account_group
        self.message_queue = asyncio.Queue()
        self.connection = Connection(self.uri, self.access_token, self.message_queue, self._connection_lost_handler)

        self._response_futures: Dict[str, asyncio.Future] = {}
        self._event_callbacks: Dict[int, List[Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]]] = defaultdict(list)
        self._is_running = False
        self._processing_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._reconnect_task: Optional[asyncio.Task] = None
        self._log_raw_messages = log_raw_messages
        self._raw_log_file = "logs/message_logbook.md"

        # --- API Modules ---
        self.balance = balance.BalanceAPI(self)
        self.market = market.MarketAPI(self)
        self.trade = trade.TradeAPI(self)

        # --- Internal State ---
        self._latest_balance: Dict[str, Any] = {}
        self.account_id = account_id
        self.account_group = account_group
        self._reconnect_attempts = 0
        self._max_reconnect_delay = 60 # Max 1 minute between attempts

    async def start(self):
        logger.info("Starting OlympTradeClient...")
        if self._is_running:
            logger.warning("Client is already running.")
            return

        self._is_running = True
        try:
            await self._connect_and_setup()
        except Exception as e:
            logger.error(f"Initial connection failed: {e}")
            # Even if initial connection fails, we start the reconnect loop if _is_running is True
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _connect_and_setup(self):
        """Internal method to handle connection and initial setup."""
        await self.connection.connect()

        # Start processing tasks if not already running
        if self._processing_task is None or self._processing_task.done():
            self._processing_task = asyncio.create_task(self._process_messages())
        if self._ping_task is None or self._ping_task.done():
            self._ping_task = asyncio.create_task(self._ping_loop())

        # Perform session initialization
        await self.initialize_session()
        self._reconnect_attempts = 0 # Reset attempts on successful setup
        logger.info("Client connected and session initialized.")

    async def stop(self):
        logger.info("Stopping OlympTradeClient...")
        self._is_running = False

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
        if self._processing_task and not self._processing_task.done():
            self._processing_task.cancel()

        await self.connection.disconnect()
        logger.info("Client stopped.")

    async def _connection_lost_handler(self):
        """Callback executed by Connection when the websocket closes unexpectedly."""
        logger.warning("Connection lost. Initiating auto-reconnect...")

        # Clean up pending futures with an error
        for fut in list(self._response_futures.values()):
            if not fut.done():
                fut.set_exception(ConnectionError("WebSocket connection lost"))
        self._response_futures.clear()

        if self._is_running:
            if self._reconnect_task is None or self._reconnect_task.done():
                self._reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self):
        """Handles automatic reconnection with exponential backoff."""
        logger.info("Reconnect loop started.")
        while self._is_running:
            if self.connection.is_connected:
                await asyncio.sleep(5)
                continue

            self._reconnect_attempts += 1
            delay = min(2 ** self._reconnect_attempts, self._max_reconnect_delay)
            logger.info(f"Reconnection attempt {self._reconnect_attempts} in {delay} seconds...")
            await asyncio.sleep(delay)

            try:
                await self._connect_and_setup()
                logger.info("Reconnection successful.")
            except Exception as e:
                logger.error(f"Reconnection attempt {self._reconnect_attempts} failed: {e}")

    def register_callback(self, event_code: int, callback: Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]):
        self._event_callbacks[event_code].append(callback)

    async def send_request(self, event_code: int, data: Any, requires_response: bool = True, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        if not self.connection.is_connected:
            raise ConnectionError("Not connected")

        request_uuid = generate_uuid() if requires_response else None
        message_str = format_message(event_code, data, request_uuid)

        future = None
        if requires_response and request_uuid:
            future = asyncio.get_running_loop().create_future()
            self._response_futures[request_uuid] = future

        try:
            await self.connection.send(message_str)
        except Exception as e:
            if request_uuid in self._response_futures:
                del self._response_futures[request_uuid]
            raise

        if future:
            try:
                response_timeout = timeout if timeout is not None else parameters.DEFAULT_RESPONSE_TIMEOUT
                return await asyncio.wait_for(future, timeout=response_timeout)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                if request_uuid in self._response_futures:
                     del self._response_futures[request_uuid]
                raise
        return None

    async def _process_messages(self):
        while self._is_running:
            try:
                raw_message = await self.message_queue.get()
                parsed_messages = parse_message(raw_message)
                if not parsed_messages:
                    continue
                for message in parsed_messages:
                    await self._dispatch_message(message)
            except asyncio.CancelledError:
                 break
            except Exception as e:
                logger.exception(f"Error processing message queue: {e}")
                await asyncio.sleep(1)

    async def _dispatch_message(self, message: Dict[str, Any]):
        request_uuid = message.get("uuid")
        event_code = message.get("e")

        if request_uuid and request_uuid in self._response_futures:
            future = self._response_futures.pop(request_uuid)
            if not future.done():
                future.set_result(message)
            return

        if event_code == settings.E_BALANCE_UPDATE:
            self._latest_balance = message

        if event_code in self._event_callbacks:
            for cb in self._event_callbacks[event_code]:
                asyncio.create_task(cb(message))

    async def _ping_loop(self):
        while self._is_running:
            try:
                await asyncio.sleep(parameters.PING_INTERVAL)
                if self.connection.is_connected:
                    await self.send_request(settings.E_PING, {}, requires_response=True, timeout=5)
            except asyncio.CancelledError:
                break
            except Exception:
                 pass

    async def initialize_session(self):
        """Mimics the browser's startup sequence for subcription and account discovery."""
        logger.info("Initializing session...")
        startup_subscriptions = [[220], [110,700,112,140,1038,1037,1039,141,22,26,111], [1054,1076,1301,1097], [141,241], [230,231], [75], [1055], [2223,2301,55,150,152,151,126,602,601], [2076], [126]]
        for sub in startup_subscriptions:
            await self.send_request(98, sub, requires_response=False)

        for group in ["demo", "real"]:
            try:
                resp = await self.send_request(1068, [{"group": group}], requires_response=True)
                if resp and 'd' in resp and resp['d']:
                    self.account_id = resp['d'][0].get('account_id')
                    self.account_group = group
                    logger.info(f"Using account_id: {self.account_id} ({group})")
                    break
            except Exception:
                continue

        if self.account_id:
            await self.send_request(1043, [{"account_id": self.account_id, "group": self.account_group}], requires_response=True)

    @property
    def current_balance_value(self) -> float:
        """Helper to get balance value as float."""
        if self._latest_balance and 'd' in self._latest_balance:
            accounts = self._latest_balance['d']
            for acc in accounts:
                if acc.get('id') == self.account_id:
                    return float(acc.get('balance', 0.0))
        return 0.0
