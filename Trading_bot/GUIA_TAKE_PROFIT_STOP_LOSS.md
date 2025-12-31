# Guía: Take Profit y Stop Loss

## 🎯 Nueva Funcionalidad Añadida

El bot ahora soporta **Take Profit** (TP) y **Stop Loss** (SL), permitiéndote gestionar el riesgo automáticamente en cada operación. Cuando incluyes estos parámetros, Alpaca crea automáticamente órdenes "bracket" que se ejecutan cuando el precio alcanza tus objetivos.

## 📊 ¿Qué son Take Profit y Stop Loss?

### Take Profit (Tomar Ganancia)
Es el precio al que quieres **cerrar la posición con ganancia**. Cuando el precio alcanza este nivel, la orden se ejecuta automáticamente y aseguras tus beneficios.

**Ejemplo:** Compras AAPL a $150. Pones `take_profit: 160`. Si el precio sube a $160, se vende automáticamente con $10 de ganancia por acción.

### Stop Loss (Detener Pérdida)
Es el precio al que quieres **cerrar la posición para limitar pérdidas**. Cuando el precio cae a este nivel, la orden se ejecuta automáticamente para evitar mayores pérdidas.

**Ejemplo:** Compras AAPL a $150. Pones `stop_loss: 145`. Si el precio baja a $145, se vende automáticamente limitando la pérdida a $5 por acción.

## 📋 Formatos JSON Disponibles

### 1. Solo Take Profit

Asegura ganancias sin límite de pérdidas.

```json
{
  "secret": "tu_secreto",
  "action": "buy",
  "symbol": "TSLA",
  "quantity": 5,
  "order_type": "market",
  "take_profit": 250.00
}
```

**Cuándo usar:** Cuando confías en que el precio subirá y no quieres un stop loss que te saque prematuramente.

### 2. Solo Stop Loss

Limita pérdidas sin techo de ganancias.

```json
{
  "secret": "tu_secreto",
  "action": "buy",
  "symbol": "NVDA",
  "quantity": 10,
  "order_type": "market",
  "stop_loss": 120.00
}
```

**Cuándo usar:** Cuando quieres protección contra caídas pero prefieres cerrar manualmente las ganancias.

### 3. Take Profit y Stop Loss (Recomendado)

Gestión completa del riesgo con límite de ganancia y pérdida.

```json
{
  "secret": "tu_secreto",
  "action": "buy",
  "symbol": "AAPL",
  "quantity": 10,
  "order_type": "market",
  "take_profit": 200.00,
  "stop_loss": 145.00
}
```

**Cuándo usar:** La mayoría de las operaciones. Define tu riesgo-beneficio antes de entrar.

### 4. Orden Límite con TP y SL

Combina entrada a precio específico con gestión de riesgo.

```json
{
  "secret": "tu_secreto",
  "action": "buy",
  "symbol": "SPY",
  "quantity": 20,
  "order_type": "limit",
  "limit_price": 450.00,
  "take_profit": 460.00,
  "stop_loss": 445.00
}
```

**Cuándo usar:** Cuando quieres entrar solo a un precio específico y gestionar el riesgo automáticamente.

## 💡 Ejemplos Prácticos

### Ejemplo 1: Trading Intradía con Ratio 2:1

Compras AAPL a precio de mercado, buscas $10 de ganancia y arriesgas $5.

```json
{
  "secret": "mi_secreto_123",
  "action": "buy",
  "symbol": "AAPL",
  "quantity": 10,
  "order_type": "market",
  "take_profit": 160.00,
  "stop_loss": 155.00
}
```

Si el precio actual es $155:
- **Ganancia potencial:** $160 - $155 = $5 por acción = $50 total
- **Pérdida máxima:** $155 - $155 = $0 (entrada a mercado podría ser ligeramente diferente)
- **Ratio riesgo-beneficio:** Depende del precio de entrada real

### Ejemplo 2: Swing Trading con Protección

Compras TSLA esperando una subida de varios días, pero proteges contra caídas.

```json
{
  "secret": "mi_secreto_123",
  "action": "buy",
  "symbol": "TSLA",
  "quantity": 5,
  "order_type": "limit",
  "limit_price": 240.00,
  "take_profit": 260.00,
  "stop_loss": 230.00
}
```

- **Entrada:** Solo si el precio llega a $240
- **Ganancia objetivo:** $260 - $240 = $20 por acción = $100 total
- **Pérdida máxima:** $240 - $230 = $10 por acción = $50 total
- **Ratio riesgo-beneficio:** 2:1 (arriesgas $50 para ganar $100)

### Ejemplo 3: Venta en Corto con Protección

Vendes NVDA esperando una caída, con límites de ganancia y pérdida.

```json
{
  "secret": "mi_secreto_123",
  "action": "sell",
  "symbol": "NVDA",
  "quantity": 10,
  "order_type": "market",
  "take_profit": 120.00,
  "stop_loss": 135.00
}
```

Si vendes a $130:
- **Ganancia objetivo:** $130 - $120 = $10 por acción = $100 total
- **Pérdida máxima:** $135 - $130 = $5 por acción = $50 total

## ⚠️ Consideraciones Importantes

### 1. Precios Lógicos

**Para órdenes de COMPRA (buy):**
- `take_profit` debe ser **mayor** que el precio de entrada
- `stop_loss` debe ser **menor** que el precio de entrada

**Para órdenes de VENTA (sell):**
- `take_profit` debe ser **menor** que el precio de entrada
- `stop_loss` debe ser **mayor** que el precio de entrada

### 2. Órdenes Bracket

Cuando incluyes `take_profit` o `stop_loss`, Alpaca crea una "orden bracket" que consiste en:
1. **Orden principal:** Tu compra o venta
2. **Orden de take profit:** Se activa si el precio alcanza tu objetivo
3. **Orden de stop loss:** Se activa si el precio alcanza tu límite de pérdida

**Solo una de las dos órdenes secundarias se ejecutará.** Cuando una se ejecuta, la otra se cancela automáticamente.

### 3. Horario del Mercado

Las órdenes bracket solo funcionan durante el horario regular del mercado (09:30 - 16:00 ET). No se ejecutan en pre-market o after-hours.

### 4. Volatilidad

En mercados muy volátiles, el precio de ejecución del stop loss puede ser diferente al precio configurado (slippage). Esto es normal y ocurre con todas las órdenes stop.

## 🔧 Cómo Actualizar

### Archivos que Debes Reemplazar

1. **`app.py`**: Contiene la nueva lógica para procesar TP y SL
2. **`templates/index.html`**: Incluye los nuevos ejemplos en la pestaña "Ejemplos"

### Pasos de Actualización

1. **Cierra el bot** si está corriendo
2. **Haz backup** de tu carpeta actual (opcional pero recomendado)
3. **Copia** el nuevo `app.py` a la raíz de tu bot
4. **Copia** el nuevo `index.html` a la carpeta `templates`
5. **Reinicia el bot**
6. **Abre** `http://localhost:5000` y ve a la pestaña "Ejemplos"

**Tu configuración (API keys) no se perderá** porque está en `config.json`.

## 📊 Verificación

Después de actualizar:

1. Ve a la pestaña **"Ejemplos"** en la interfaz web
2. Deberías ver 6 ejemplos:
   - Orden a Mercado
   - Orden Límite
   - **Con Take Profit** (nuevo)
   - **Con Stop Loss** (nuevo)
   - **Con Take Profit y Stop Loss** (nuevo)
   - **Orden Límite con TP y SL** (nuevo)
   - Con Variables de TradingView

3. Usa la pestaña **"Prueba"** para probar un JSON con TP y SL:

```json
{
  "secret": "tu_secreto",
  "action": "buy",
  "symbol": "AAPL",
  "quantity": 1,
  "order_type": "market",
  "take_profit": 200.00,
  "stop_loss": 145.00
}
```

Si recibes un mensaje de éxito, ¡la funcionalidad está activa!

## 🎓 Mejores Prácticas

### 1. Siempre Usa Stop Loss

Protege tu capital. Nunca entres en una operación sin saber cuánto estás dispuesto a perder.

### 2. Ratio Riesgo-Beneficio Mínimo 1:2

Busca ganar al menos el doble de lo que arriesgas. Ejemplo:
- Arriesgas $5 por acción → Busca ganar $10 por acción

### 3. Calcula el Tamaño de Posición

No arriesgues más del 1-2% de tu capital en una sola operación.

**Ejemplo:**
- Capital: $10,000
- Riesgo máximo por operación: 2% = $200
- Stop loss: $5 por acción
- Tamaño de posición: $200 / $5 = 40 acciones

### 4. Prueba en Paper Trading Primero

Antes de usar dinero real, prueba tus estrategias con la cuenta Paper de Alpaca.

## 🆘 Solución de Problemas

### Error: "order_class not supported"

**Causa:** Tu cuenta de Alpaca no soporta órdenes bracket.

**Solución:** Verifica que estés usando una cuenta que permita órdenes avanzadas. Las cuentas básicas de Alpaca soportan bracket orders, pero algunas restricciones pueden aplicar.

### Error: "take_profit price invalid"

**Causa:** El precio de take profit no es lógico para el tipo de orden.

**Solución:** 
- Para BUY: `take_profit` > precio de entrada
- Para SELL: `take_profit` < precio de entrada

### La Orden se Ejecuta Pero no Veo TP/SL

**Causa:** Puede que estés revisando durante after-hours.

**Solución:** Las órdenes bracket solo se activan durante horario regular del mercado.

## 📚 Recursos Adicionales

- [Documentación de Alpaca sobre Bracket Orders](https://alpaca.markets/docs/trading/orders/#bracket-orders)
- Revisa el archivo `trading_bot.log` para ver detalles de las órdenes ejecutadas
- Usa la pestaña "Estado" en la interfaz para verificar tu conexión con Alpaca
