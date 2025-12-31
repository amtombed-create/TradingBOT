# Guía de Diagnóstico: ¿Por qué no llegan las órdenes de TradingView?

Si has configurado todo pero las órdenes no se ejecutan, no te preocupes. Vamos a seguir un proceso de diagnóstico paso a paso para encontrar y solucionar el problema. La comunicación entre TradingView y tu bot sigue esta ruta:

```mermaid
graph TD
    A[TradingView] -- 1. Envía Alerta --> B(Internet);
    B -- 2. Llega a Ngrok --> C{URL Pública de Ngrok};
    C -- 3. Redirige a tu PC --> D[Bot Local (app.py)];
    D -- 4. Procesa y Valida --> E(API de Alpaca);
```

Un fallo en cualquiera de estos 4 pasos impedirá que la orden se ejecute. Sigue esta lista de verificación en orden.

## ✅ Checklist de Diagnóstico Rápido

| Punto de Verificación | ¿Qué hacer? | Estado |
| :--- | :--- | :--- |
| **1. Bot en Ejecución** | Revisa la terminal donde iniciaste el bot. ¿Sigue activa? ¿Ves algún error? | ☐ |
| **2. Ngrok Activo** | Revisa la terminal de Ngrok. ¿Sigue activa? ¿Muestra "Online"? | ☐ |
| **3. Peticiones en Ngrok** | En la terminal de Ngrok, ¿ves alguna línea cuando se dispara la alerta de TV? | ☐ |
| **4. URL en TradingView** | Compara la URL de Ngrok con la que tienes en la alerta de TV. ¿Son idénticas? | ☐ |
| **5. Formato del Mensaje** | Revisa el JSON en el mensaje de la alerta de TV. ¿Tiene la sintaxis correcta? | ☐ |
| **6. Secreto del Webhook** | Compara el `secret` en el JSON de TV con el que guardaste en la interfaz web. ¿Son idénticos? | ☐ |

---

## 🔍 Diagnóstico Detallado

### Paso 1: Verificar que el Bot está Corriendo

**Cómo verificar:**

1.  Busca la ventana de terminal o PowerShell donde ejecutaste `python app.py` o el script de inicio.
2.  **Señal de que funciona:** Deberías ver líneas como `* Running on http://127.0.0.1:5000` y no debería haber mensajes de error recientes.
3.  **Señal de que NO funciona:** La ventana está cerrada, o ves un mensaje de error largo (un `Traceback`).

**Solución:**

*   Si la ventana está cerrada, vuelve a iniciar el bot (`INICIAR_BOT.bat` o `./iniciar_bot.sh`).
*   Si hay un error, copia el mensaje de error. A menudo indica el problema (ej: un error de sintaxis).

### Paso 2: Verificar que Ngrok está Activo y Online

**Cómo verificar:**

1.  Busca la ventana de terminal donde ejecutaste `ngrok http 5000`.
2.  **Señal de que funciona:** Deberías ver una interfaz con el estado `online` y tu URL pública (`https://....ngrok.io`).
3.  **Señal de que NO funciona:** La ventana está cerrada, o muestra un estado `offline` o `reconnecting`.

**Solución:**

*   Si está cerrado, vuelve a iniciar Ngrok. **Recuerda que Ngrok te dará una NUEVA URL cada vez que lo inicies**, por lo que tendrás que actualizarla en TradingView.
*   Si tienes problemas de conexión, revisa tu internet.

### Paso 3: Revisar el Tráfico en Ngrok (El Paso Más Importante)

Esta es la prueba definitiva para saber si TradingView está logrando comunicarse con tu ordenador.

**Cómo verificar:**

1.  Mantén la ventana de la terminal de Ngrok visible.
2.  Ve a TradingView y dispara una alerta manualmente (puedes mover una línea de precio para que se cruce).
3.  Observa la sección "HTTP Requests" en la terminal de Ngrok.

**Interpretación de los resultados:**

*   **Aparece una nueva línea con `200 OK`**:
    *   **Diagnóstico:** ¡Buenas noticias! La conexión funciona perfectamente. TradingView está enviando la alerta y tu bot la está recibiendo y procesando. Si la orden no se ejecuta, el problema está en el **contenido del mensaje** (Paso 5 y 6) o en la lógica de la orden (revisa el archivo `trading_bot.log`).

*   **Aparece una nueva línea con un error `4xx` o `5xx` (ej: `403 Forbidden`, `400 Bad Request`)**:
    *   **Diagnóstico:** La conexión funciona, pero tu bot está rechazando la petición. La causa más común es un **secreto de webhook incorrecto** (`403 Forbidden`) o un **JSON mal formado** (`400 Bad Request`). Ve directamente a los Pasos 5 y 6.

*   **NO aparece ninguna línea nueva**:
    *   **Diagnóstico:** La alerta de TradingView **NUNCA** está llegando a tu ordenador. El problema está en la configuración de TradingView (Paso 4) o en alguna red/firewall que bloquea la salida.

### Paso 4: Verificar la URL del Webhook en TradingView

Si no aparece nada en Ngrok, el error más común es una URL incorrecta.

**Cómo verificar:**

1.  En la terminal de Ngrok, copia la URL `Forwarding` que empieza por `https://`.
2.  En TradingView, edita tu alerta y ve a la pestaña "Notificaciones".
3.  Pega la URL de Ngrok en un bloc de notas y, debajo, pega la URL que tienes en TradingView.
4.  **Compáralas carácter por carácter.**

**Errores comunes a buscar:**

*   Olvidar añadir `/webhook` al final de la URL en TradingView.
*   Un error de tipeo (una letra o número incorrecto).
*   Usar `http` en lugar de `https`.
*   No haber actualizado la URL de Ngrok después de reiniciarlo.

### Paso 5: Verificar el Formato del Mensaje (JSON)

Si Ngrok muestra un error `400 Bad Request`, el problema casi seguro está aquí.

**Cómo verificar:**

1.  Copia el contenido del campo "Mensaje" de tu alerta de TradingView.
2.  Pégalo en un validador de JSON online como [JSONLint](https://jsonlint.com/).

**Errores comunes a buscar:**

*   Falta una coma `,` entre elementos.
*   Hay una coma `,` extra en el último elemento.
*   Las claves y los valores de tipo texto no están entre comillas dobles `"`.
*   Usar comillas simples `'` en lugar de comillas dobles `"`.

**Correcto:**
```json
{
  "secret": "mi_secreto_123",
  "action": "buy",
  "symbol": "AAPL",
  "quantity": "1"
}
```

**Incorrecto (falta coma):**
```json
{
  "secret": "mi_secreto_123"
  "action": "buy",
  "symbol": "AAPL",
  "quantity": "1"
}
```

### Paso 6: Verificar el Secreto del Webhook

Si Ngrok muestra un error `403 Forbidden`, el problema es el secreto.

**Cómo verificar:**

1.  Ve a la interfaz web del bot (`http://localhost:5000`).
2.  Mira el valor que tienes en el campo "Secreto del Webhook".
3.  Compara ese valor con el que tienes en el campo `"secret"` dentro del JSON de tu alerta de TradingView.

**Deben ser absolutamente idénticos**, incluyendo mayúsculas, minúsculas y espacios.

## 🪵 Usando el Archivo de Log

Si Ngrok muestra `200 OK` pero la orden no aparece en Alpaca, el archivo `trading_bot.log` es tu mejor amigo.

1.  En la carpeta del bot, abre el archivo `trading_bot.log` con un editor de texto.
2.  Busca la entrada más reciente.

*   **Si ves `Webhook recibido:` seguido de tu JSON**, significa que el bot recibió la alerta.
*   **Si después de eso ves `Orden ejecutada exitosamente:`**, la orden se envió a Alpaca. Si no la ves en tu cuenta, podría haber sido rechazada por Alpaca por falta de fondos, por intentar operar un activo no válido, etc.
*   **Si ves un error**, el mensaje te dirá qué falló (ej: "Credenciales de Alpaca no configuradas", "símbolo no válido", etc.).

## 🆕 Herramienta de Prueba de Webhook

Para facilitar el diagnóstico, he añadido una nueva herramienta a la interfaz web que te permite simular una alerta de TradingView sin usar Ngrok ni TradingView. Esto es perfecto para verificar que tu bot y la configuración del mensaje son correctos.

1.  Ve a `http://localhost:5000`.
2.  Busca la nueva sección **"🔬 Prueba de Webhook Manual"**.
3.  Pega el JSON de tu alerta en el área de texto.
4.  Haz clic en **"Enviar Webhook de Prueba"**.

*   **Si obtienes un mensaje de éxito**, sabes que tu bot y tu JSON funcionan. El problema debe estar en la conexión con Ngrok o la configuración de TradingView.
*   **Si obtienes un error**, el mensaje te dirá exactamente qué está mal en tu JSON (formato, secreto, etc.), permitiéndote corregirlo fácilmente.
