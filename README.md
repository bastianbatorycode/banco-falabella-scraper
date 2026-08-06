\# Banco Falabella API

API REST de solo lectura para consultar una Cuenta Corriente de Banco Falabella.

Permite:

\- Obtener los períodos disponibles.  
\- Consultar movimientos entre dos períodos.  
\- Consultar el saldo disponible.

\#\# URL base

\`\`\`text  
http://localhost:5000  
\`\`\`

Desde otro equipo de la red:

\`\`\`text  
http://IP\_DEL\_SERVIDOR:5000  
\`\`\`

Todas las solicitudes deben usar:

\`\`\`http  
Content-Type: application/json  
\`\`\`

\#\# Credenciales

Las credenciales se leen exclusivamente desde variables de entorno:

\`\`\`env  
USERNAME=TU\_USUARIO  
PASSWORD=TU\_CONTRASEÑA  
\`\`\`

Puedes guardarlas en un archivo \`.env\` ubicado junto a \`falabella\_api.py\`.

\`\`\`text  
banco-falabella/  
├── falabella\_api.py  
├── requirements.txt  
└── .env  
\`\`\`

Las credenciales no deben enviarse dentro de las solicitudes HTTP.

\#\# Endpoints

\#\#\# POST /periods

Obtiene los períodos disponibles para consultar movimientos.

\#\#\#\# Request

\`\`\`json  
{}  
\`\`\`

\#\#\#\# Respuesta

\`\`\`json  
{  
  "periods": \[  
    "08-2026",  
    "07-2026",  
    "06-2026"  
  \]  
}  
\`\`\`

Los períodos usan el formato \`MM-YYYY\`.

\#\#\#\# PowerShell

\`\`\`powershell  
Invoke-RestMethod \`  
    \-Method Post \`  
    \-Uri "http://localhost:5000/periods" \`  
    \-ContentType "application/json" \`  
    \-Body "{}"  
\`\`\`

\#\#\#\# curl

\`\`\`bash  
curl \-X POST http://localhost:5000/periods \\  
  \-H "Content-Type: application/json" \\  
  \-d '{}'  
\`\`\`

\#\#\# POST /movements

Obtiene los movimientos comprendidos entre dos períodos válidos.

Consulta primero \`/periods\` para obtener los valores aceptados.

\#\#\#\# Request

\`\`\`json  
{  
  "period\_start": "07-2026",  
  "period\_end": "08-2026"  
}  
\`\`\`

| Campo | Tipo | Obligatorio | Descripción |  
|---|---|---|---|  
| \`period\_start\` | string | Sí | Período inicial en formato \`MM-YYYY\`. |  
| \`period\_end\` | string | Sí | Período final en formato \`MM-YYYY\`. |

\#\#\#\# Respuesta

\`\`\`json  
{  
  "period\_start": "07-2026",  
  "period\_end": "08-2026",  
  "movements": \[  
    {  
      "description": "Ejemplo de movimiento",  
      "amount": \-15990  
    }  
  \]  
}  
\`\`\`

Los valores monetarios se devuelven como enteros, sin decimales ni separadores de miles.

\#\#\#\# PowerShell

\`\`\`powershell  
$body \= @{  
    period\_start \= "07-2026"  
    period\_end   \= "08-2026"  
} | ConvertTo-Json

Invoke-RestMethod \`  
    \-Method Post \`  
    \-Uri "http://localhost:5000/movements" \`  
    \-ContentType "application/json" \`  
    \-Body $body  
\`\`\`

\#\#\#\# curl

\`\`\`bash  
curl \-X POST http://localhost:5000/movements \\  
  \-H "Content-Type: application/json" \\  
  \-d '{  
    "period\_start": "07-2026",  
    "period\_end": "08-2026"  
  }'  
\`\`\`

\#\#\# POST /balance

Obtiene el saldo disponible actual.

\#\#\#\# Request

\`\`\`json  
{}  
\`\`\`

\#\#\#\# Respuesta

\`\`\`json  
{  
  "available\_balance": 250000  
}  
\`\`\`

\#\#\#\# PowerShell

\`\`\`powershell  
Invoke-RestMethod \`  
    \-Method Post \`  
    \-Uri "http://localhost:5000/balance" \`  
    \-ContentType "application/json" \`  
    \-Body "{}"  
\`\`\`

\#\#\#\# curl

\`\`\`bash  
curl \-X POST http://localhost:5000/balance \\  
  \-H "Content-Type: application/json" \\  
  \-d '{}'  
\`\`\`

\#\# Resumen

| Método | Endpoint | Request |  
|---|---|---|  
| \`POST\` | \`/periods\` | \`{}\` |  
| \`POST\` | \`/movements\` | \`period\_start\`, \`period\_end\` |  
| \`POST\` | \`/balance\` | \`{}\` |

\#\# Instalación

\`\`\`powershell  
python \-m pip install \-r requirements.txt  
python .\\falabella\_api.py  
\`\`\`

El servicio escucha en:

\`\`\`text  
0.0.0.0:5000  
\`\`\`
