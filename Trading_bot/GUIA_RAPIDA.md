# Gu
a R
pida de Inicio

## Pasos para Empezar (5 minutos)

### 1. Instalar Dependencias

Abre la terminal en esta carpeta y ejecuta:

```bash
pip install -r requirements.txt
```

### 2. Iniciar el Bot

**Windows**: Haz doble clic en `INICIAR_BOT.bat`

**Mac/Linux**: Ejecuta en la terminal:
```bash
./iniciar_bot.sh
```

### 3. Configurar el Bot

1. Abre tu navegador y ve a: `http://localhost:5000`
2. Introduce tus API Keys de Alpaca
3. Marca "Paper Trading" si est
s probando
4. Crea un secreto para tu webhook (ej: `mi_secreto_123`)
5. Haz clic en "Guardar Configuraci
"

### 4. Exponer con Ngrok

En una nueva terminal:

```bash
ngrok http 5000
```

Copia la URL que te da (ej: `https://xxxx.ngrok.io`)

### 5. Configurar TradingView

1. Crea una alerta en TradingView
2. En "Notificaciones" marca "URL de Webhook"
3. Pega tu URL de Ngrok + `/webhook`:
   ```
   https://xxxx.ngrok.io/webhook
   ```
4. En "Mensaje" pon:
   ```json
   {
     "secret": "mi_secreto_123",
     "action": "buy",
     "symbol": "AAPL",
     "quantity": "1",
     "order_type": "market"
   }
   ```

## 
Listo!

Cuando se dispare la alerta, tu bot ejecutar
 la orden autom
ticamente.

## Verificaci

*   Revisa `http://localhost:5000` para ver el estado
*   Revisa el archivo `trading_bot.log` para ver el historial
*   La terminal de Ngrok te muestra las peticiones recibidas

## Ayuda

Lee el archivo `README.md` completo para m
s detalles y ejemplos.
