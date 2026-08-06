# Banco Falabella API

API REST de solo lectura para consultar una Cuenta Corriente de Banco Falabella.

Permite:

- Obtener los periodos disponibles.
- Consultar movimientos entre dos periodos.
- Consultar el saldo disponible.

## URL base

```text
http://localhost:5000
```

Desde otro equipo de la red:

```text
http://IP_DEL_SERVIDOR:5000
```

Todas las solicitudes deben usar:

```http
Content-Type: application/json
```

## Credenciales

Las credenciales se leen exclusivamente desde variables de entorno:

```env
USERNAME=TU_USUARIO
PASSWORD=TU_CONTRASENA
```

Puedes guardarlas en un archivo `.env` ubicado junto a `falabella_api.py`.

Las credenciales no deben enviarse dentro de las solicitudes HTTP.

## Endpoints

### POST /periods

Obtiene los periodos disponibles para consultar movimientos.

#### Request

```json
{}
```

#### Respuesta

```json
{"periods": ["08-2026", "07-2026", "06-2026"]}
```

Los periodos usan el formato `MM-YYYY`.

### POST /movements

Obtiene los movimientos comprendidos entre dos periodos validos.

Consulta primero `/periods` para obtener los valores aceptados.

#### Request

```json
{"period_start": "07-2026", "period_end": "08-2026"}
```

| Campo | Tipo | Obligatorio | Descripcion |
|---|---|---|---|
| `period_start` | string | Si | Periodo inicial en formato `MM-YYYY`. |
| `period_end` | string | Si | Periodo final en formato `MM-YYYY`. |

Los valores monetarios se devuelven como enteros, sin decimales ni separadores de miles.

### POST /balance

Obtiene el saldo disponible actual.

#### Request

```json
{}
```

#### Respuesta

```json
{"available_balance": 250000}
```

## Resumen

| Metodo | Endpoint | Request |
|---|---|---|
| `POST` | `/periods` | `{}` |
| `POST` | `/movements` | `period_start`, `period_end` |
| `POST` | `/balance` | `{}` |

## Instalacion

```powershell
python -m pip install -r requirements.txt
python falabella_api.py
```

El servicio escucha en:

```text
0.0.0.0:5000
```