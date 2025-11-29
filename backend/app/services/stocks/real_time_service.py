# services/stocks/real_time_service.py
import asyncio
import aiohttp
import websockets
from typing import List, Dict, Any, Optional, Callable
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class StockRealTimeService:
    def __init__(self, stock_service):
        self.stock_service = stock_service
        self.connected_clients = set()
        self.subscribed_symbols = set()
    
    async def start_websocket_server(self, host: str = 'localhost', port: int = 8765):
        """
        Start WebSocket server for real-time stock data
        """
        try:
            server = await websockets.serve(
                self._handle_websocket_connection, 
                host, 
                port
            )
            logger.info(f"Stock WebSocket server started on {host}:{port}")
            return server
        except Exception as e:
            logger.error(f"Error starting WebSocket server: {str(e)}")
            return None
    
    async def _handle_websocket_connection(self, websocket, path):
        """
        Handle WebSocket connections and messages
        """
        self.connected_clients.add(websocket)
        logger.info(f"New WebSocket connection: {len(self.connected_clients)} clients connected")
        
        try:
            async for message in websocket:
                await self._process_websocket_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        finally:
            self.connected_clients.remove(websocket)
            logger.info(f"WebSocket connection removed: {len(self.connected_clients)} clients remaining")
    
    async def _process_websocket_message(self, websocket, message: str):
        """
        Process incoming WebSocket messages
        """
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'subscribe':
                symbols = data.get('symbols', [])
                await self._subscribe_symbols(websocket, symbols)
            elif action == 'unsubscribe':
                symbols = data.get('symbols', [])
                await self._unsubscribe_symbols(websocket, symbols)
            elif action == 'get_price':
                symbol = data.get('symbol')
                if symbol:
                    price_data = await self.stock_service.get_current_price(symbol)
                    await websocket.send(json.dumps({
                        'type': 'price_update',
                        'symbol': symbol,
                        'data': price_data
                    }))
            
        except json.JSONDecodeError:
            logger.error("Invalid JSON message received")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")
    
    async def _subscribe_symbols(self, websocket, symbols: List[str]):
        """
        Subscribe to real-time updates for symbols
        """
        for symbol in symbols:
            self.subscribed_symbols.add(symbol.upper())
        
        logger.info(f"Subscribed to symbols: {symbols}")
        await websocket.send(json.dumps({
            'type': 'subscription_confirmed',
            'symbols': symbols
        }))
    
    async def _unsubscribe_symbols(self, websocket, symbols: List[str]):
        """
        Unsubscribe from real-time updates
        """
        for symbol in symbols:
            if symbol.upper() in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol.upper())
        
        logger.info(f"Unsubscribed from symbols: {symbols}")
        await websocket.send(json.dumps({
            'type': 'unsubscription_confirmed',
            'symbols': symbols
        }))
    
    async def broadcast_price_update(self, symbol: str, price_data: Dict[str, Any]):
        """
        Broadcast price update to all subscribed clients
        """
        if symbol.upper() not in self.subscribed_symbols:
            return
        
        message = json.dumps({
            'type': 'price_update',
            'symbol': symbol,
            'data': price_data,
            'timestamp': datetime.now().isoformat()
        })
        
        disconnected_clients = set()
        
        for client in self.connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.connected_clients.remove(client)
    
    async def start_price_updates(self, interval_seconds: int = 30):
        """
        Start periodic price updates for subscribed symbols
        """
        while True:
            try:
                if self.subscribed_symbols and self.connected_clients:
                    symbols = list(self.subscribed_symbols)
                    
                    # Get prices for all subscribed symbols
                    for symbol in symbols:
                        price_data = await self.stock_service.get_current_price(symbol)
                        if price_data:
                            await self.broadcast_price_update(symbol, price_data)
                    
                    logger.debug(f"Sent price updates for {len(symbols)} symbols to {len(self.connected_clients)} clients")
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in price update loop: {str(e)}")
                await asyncio.sleep(60)  # Wait before retrying