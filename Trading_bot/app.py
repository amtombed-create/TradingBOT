"""
Bot de Trading: TradingView -> Alpaca
Recibe webhooks de TradingView y ejecuta órdenes en Alpaca
"""

from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import os
from datetime import datetime
import logging
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.historical import StockHistoricalDataClient
import pytz

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_cambiar_en_produccion'

# Archivos de configuración y logs
CONFIG_FILE = 'config.json'
ORDER_LOG_FILE = 'order_log.json'

# Lista en memoria para órdenes recientes (últimas 100)
order_history = []

def load_config():
    """Carga la configuración desde el archivo JSON"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        'alpaca_api_key': '',
        'alpaca_secret_key': '',
        'alpaca_paper': True,
        'webhook_secret': ''
    }

def save_config(config):
    """Guarda la configuración en el archivo JSON"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def load_order_history():
    """Carga el historial de órdenes desde el archivo JSON"""
    global order_history
    if os.path.exists(ORDER_LOG_FILE):
        try:
            with open(ORDER_LOG_FILE, 'r') as f:
                order_history = json.load(f)
                # Mantener solo las últimas 100 órdenes
                order_history = order_history[-100:]
        except:
            order_history = []
    else:
        order_history = []
    return order_history

def save_order_history():
    """Guarda el historial de órdenes en el archivo JSON"""
    with open(ORDER_LOG_FILE, 'w') as f:
        json.dump(order_history[-100:], f, indent=2)

def add_order_to_history(order_data):
    """Añade una orden al historial"""
    global order_history
    order_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': order_data.get('action'),
        'symbol': order_data.get('symbol'),
        'quantity': order_data.get('quantity'),
        'order_type': order_data.get('order_type'),
        'limit_price': order_data.get('limit_price'),
        'take_profit': order_data.get('take_profit'),
        'stop_loss': order_data.get('stop_loss'),
        'status': 'pending'
    }
    order_history.append(order_entry)
    order_history = order_history[-100:]  # Mantener solo las últimas 100
    save_order_history()
    return order_entry

def update_order_status(index, status, details=None):
    """Actualiza el estado de una orden en el historial"""
    global order_history
    if 0 <= index < len(order_history):
        order_history[index]['status'] = status
        if details:
            order_history[index]['details'] = details
        save_order_history()

def get_alpaca_client():
    """Crea y retorna un cliente de Alpaca con las credenciales configuradas"""
    config = load_config()
    
    if not config['alpaca_api_key'] or not config['alpaca_secret_key']:
        raise ValueError("Las credenciales de Alpaca no están configuradas")
    
    return TradingClient(
        api_key=config['alpaca_api_key'],
        secret_key=config['alpaca_secret_key'],
        paper=config['alpaca_paper']
    )

@app.route('/')
def index():
    """Página principal con la interfaz de configuración"""
    config = load_config()
    return render_template('index.html', config=config)

@app.route('/config', methods=['POST'])
def update_config():
    """Actualiza la configuración de las API keys"""
    try:
        config = {
            'alpaca_api_key': request.form.get('alpaca_api_key', ''),
            'alpaca_secret_key': request.form.get('alpaca_secret_key', ''),
            'alpaca_paper': request.form.get('alpaca_paper') == 'on',
            'webhook_secret': request.form.get('webhook_secret', '')
        }
        
        save_config(config)
        logging.info("Configuración actualizada exitosamente")
        
        return redirect(url_for('index'))
    except Exception as e:
        logging.error(f"Error al actualizar configuración: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Endpoint que recibe las alertas de TradingView
    
    Formato esperado del JSON de TradingView:
    {
        "secret": "tu_secreto_webhook",
        "action": "buy" o "sell",
        "symbol": "AAPL",
        "quantity": 10,
        "order_type": "market" o "limit",
        "limit_price": 150.00 (opcional, solo para órdenes limit),
        "take_profit": 160.00 (opcional),
        "stop_loss": 145.00 (opcional)
    }
    """
    try:
        # Obtener datos del webhook
        data = request.get_json()
        
        if not data:
            logging.warning("Webhook recibido sin datos")
            return jsonify({'error': 'No se recibieron datos'}), 400
        
        logging.info(f"Webhook recibido: {json.dumps(data, indent=2)}")
        
        # Verificar secreto del webhook
        config = load_config()
        if config['webhook_secret']:
            if data.get('secret') != config['webhook_secret']:
                logging.warning("Intento de acceso con secreto incorrecto")
                return jsonify({'error': 'Secreto inválido'}), 403
        
        # Validar campos requeridos
        required_fields = ['action', 'symbol', 'quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido faltante: {field}'}), 400
        
        # Extraer información de la orden
        action = data['action'].lower()
        symbol = data['symbol'].upper()
        quantity = int(data['quantity'])
        order_type = data.get('order_type', 'market').lower()
        limit_price = data.get('limit_price')
        take_profit = data.get('take_profit')
        stop_loss = data.get('stop_loss')
        
        # Registrar la orden en el historial
        order_index = len(order_history)
        add_order_to_history(data)
        
        # Validar acción
        if action not in ['buy', 'sell']:
            return jsonify({'error': 'Acción debe ser "buy" o "sell"'}), 400
        
        # Crear cliente de Alpaca
        try:
            trading_client = get_alpaca_client()
        except ValueError as e:
            logging.error(f"Error de configuración: {str(e)}")
            return jsonify({'error': 'Credenciales de Alpaca no configuradas'}), 500
        
        # Determinar el lado de la orden
        side = OrderSide.BUY if action == 'buy' else OrderSide.SELL
        
        # Preparar órdenes bracket (take profit y stop loss)
        # Bracket orders requieren AMBOS take_profit Y stop_loss
        # Si solo hay stop_loss, usamos 'oto' (one-triggers-other)
        order_class = None
        if take_profit and stop_loss:
            order_class = 'bracket'
        elif stop_loss and not take_profit:
            order_class = 'oto'
        
        # Crear la orden según el tipo
        if order_type == 'market':
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
                order_class=order_class if order_class else None,
                take_profit={'limit_price': float(take_profit)} if take_profit else None,
                stop_loss={'stop_price': float(stop_loss)} if stop_loss else None
            )
        elif order_type == 'limit':
            if not limit_price:
                return jsonify({'error': 'limit_price requerido para órdenes limit'}), 400
            
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=float(limit_price),
                order_class=order_class if order_class else None,
                take_profit={'limit_price': float(take_profit)} if take_profit else None,
                stop_loss={'stop_price': float(stop_loss)} if stop_loss else None
            )
        else:
            return jsonify({'error': 'order_type debe ser "market" o "limit"'}), 400
        
        # Enviar orden a Alpaca
        order = trading_client.submit_order(order_request)
        
        logging.info(f"Orden ejecutada exitosamente: {order.id}")
        
        # Actualizar estado de la orden en el historial
        update_order_status(order_index, 'success', {
            'order_id': str(order.id),  # Convertir UUID a string
            'status': order.status
        })
        
        response_data = {
            'success': True,
            'order_id': str(order.id),  # Convertir UUID a string
            'symbol': symbol,
            'action': action,
            'quantity': quantity,
            'status': order.status,
            'timestamp': datetime.now().isoformat()
        }
        
        # Añadir información de take profit y stop loss si existen
        if take_profit:
            response_data['take_profit'] = take_profit
        if stop_loss:
            response_data['stop_loss'] = stop_loss
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error al procesar webhook: {str(e)}")
        
        # Actualizar estado de la orden en el historial como error
        if 'order_index' in locals():
            update_order_status(order_index, 'error', {'error': str(e)})
        
        return jsonify({
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/save_config', methods=['POST'])
def save_config_endpoint():
    """Endpoint para guardar la configuración desde la interfaz actualizada"""
    try:
        data = request.get_json()
        
        config = {
            'alpaca_api_key': data.get('api_key', ''),
            'alpaca_secret_key': data.get('api_secret', ''),
            'alpaca_paper': data.get('paper_trading', 'true') == 'true',
            'webhook_secret': data.get('webhook_secret', '')
        }
        
        save_config(config)
        logging.info("Configuración guardada exitosamente")
        
        return jsonify({'success': True, 'message': 'Configuración guardada correctamente'})
    except Exception as e:
        logging.error(f"Error al guardar configuración: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/test_connection', methods=['GET'])
def test_connection():
    """Endpoint para probar la conexión con Alpaca"""
    try:
        client = get_alpaca_client()
        account = client.get_account()
        
        return jsonify({
            'success': True,
            'account': {
                'equity': str(account.equity),
                'cash': str(account.cash),
                'buying_power': str(account.buying_power)
            }
        })
    except Exception as e:
        logging.error(f"Error al probar conexión: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/status')
def status():
    """Endpoint para verificar el estado del bot"""
    config = load_config()
    
    # Verificar si las credenciales están configuradas
    credentials_configured = bool(config['alpaca_api_key'] and config['alpaca_secret_key'])
    
    # Intentar conectar con Alpaca si las credenciales están configuradas
    alpaca_connected = False
    account_info = None
    market_info = None
    
    if credentials_configured:
        try:
            trading_client = get_alpaca_client()
            account = trading_client.get_account()
            alpaca_connected = True
            account_info = {
                'account_number': account.account_number,
                'status': account.status,
                'buying_power': float(account.buying_power),
                'cash': float(account.cash),
                'portfolio_value': float(account.portfolio_value)
            }
            
            # Obtener información del reloj del mercado
            clock = trading_client.get_clock()
            
            # Zona horaria de Nueva York (donde opera el mercado de EE.UU.)
            ny_tz = pytz.timezone('America/New_York')
            now_ny = datetime.now(ny_tz)
            
            # Calcular próxima apertura y cierre
            next_open = clock.next_open.astimezone(ny_tz) if clock.next_open else None
            next_close = clock.next_close.astimezone(ny_tz) if clock.next_close else None
            
            market_info = {
                'is_open': clock.is_open,
                'next_open': next_open.strftime('%Y-%m-%d %H:%M:%S %Z') if next_open else None,
                'next_close': next_close.strftime('%Y-%m-%d %H:%M:%S %Z') if next_close else None,
                'current_time': now_ny.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'timezone': 'America/New_York',
                'regular_hours': '09:30 - 16:00 ET',
                'trading_days': 'Lunes a Viernes (excepto festivos)'
            }
            
        except Exception as e:
            logging.error(f"Error al conectar con Alpaca: {str(e)}")
    
    return jsonify({
        'bot_status': 'running',
        'credentials_configured': credentials_configured,
        'alpaca_connected': alpaca_connected,
        'account_info': account_info,
        'market_info': market_info,
        'paper_trading': config['alpaca_paper'],
        'webhook_secret_configured': bool(config['webhook_secret']),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/orders', methods=['GET'])
def get_orders():
    """Endpoint para obtener el historial de órdenes"""
    try:
        # Devolver las órdenes en orden inverso (más recientes primero)
        return jsonify({
            'success': True,
            'orders': list(reversed(order_history)),
            'count': len(order_history)
        })
    except Exception as e:
        logging.error(f"Error al obtener historial de órdenes: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['POST'])
def test_order():
    """Endpoint para probar una orden manualmente"""
    try:
        data = request.get_json()
        
        trading_client = get_alpaca_client()
        
        # Crear una orden de prueba (compra de 1 acción)
        symbol = data.get('symbol', 'AAPL')
        
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=1,
            side=OrderSide.BUY,
            time_in_force=TimeInForce.DAY
        )
        
        order = trading_client.submit_order(order_request)
        
        return jsonify({
            'success': True,
            'order_id': order.id,
            'message': f'Orden de prueba enviada para {symbol}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Crear directorio de templates si no existe
    os.makedirs('templates', exist_ok=True)
    
    # Cargar historial de órdenes
    load_order_history()
    logging.info(f"Historial de órdenes cargado: {len(order_history)} órdenes")
    
    # Iniciar servidor Flask
    logging.info("Iniciando bot de trading TradingView -> Alpaca")
    logging.info("Servidor Flask corriendo en http://localhost:5000")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
