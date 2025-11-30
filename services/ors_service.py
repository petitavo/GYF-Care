# services/ors_service.py
import os
import requests
import time
from typing import Optional, Dict, Tuple
from pathlib import Path
import json

# ============================================
# CONFIGURACIÓN DE OPENROUTESERVICE
# ============================================
ORS_API_KEY = os.getenv(
    "ORS_API_KEY",
    "eyJvcmciOiI1YjNjZTM1OTc4NTExMDAwMDFjZjYyNDgiLCJpZCI6IjdjNDczMzkwZmIzNDQxMGZiNWFiNWE5YjcyMTg1MjI2IiwiaCI6Im11cm11cjY0In0="
)
ORS_BASE_URL = os.getenv("ORS_BASE_URL", "https://api.openrouteservice.org")
ORS_TIMEOUT = int(os.getenv("ORS_TIMEOUT", "30"))  # Aumentado a 30s
ORS_MAX_RETRIES = int(os.getenv("ORS_MAX_RETRIES", "3"))

# Cache
CACHE_DIR = Path("cache")
ENABLE_CACHE = True


class ORSService:
    """Servicio para calcular rutas reales usando OpenRouteService."""

    def __init__(self):
        self.api_key = ORS_API_KEY
        self.base_url = ORS_BASE_URL
        self.endpoint = f"{self.base_url}/v2/directions/driving-car"
        self.timeout = ORS_TIMEOUT
        self.max_retries = ORS_MAX_RETRIES

        # Crear directorio de caché
        if ENABLE_CACHE:
            CACHE_DIR.mkdir(exist_ok=True)

        # Log de inicialización
        print("=" * 60)
        print(" ORS SERVICE INITIALIZED")
        print("=" * 60)
        print(f" Base URL: {self.base_url}")
        print(f" API Key: {self.api_key[:20]}...{self.api_key[-10:]}")
        print(f"⏱  Timeout: {self.timeout}s")
        print(f" Max Retries: {self.max_retries}")
        print(f" Cache: {'Enabled' if ENABLE_CACHE else 'Disabled'}")
        print("=" * 60)

    def _get_cache_path(self, start_lat: float, start_lon: float, 
                       end_lat: float, end_lon: float) -> Path:
        """Genera path del archivo de caché."""
        cache_key = f"{start_lat:.6f}_{start_lon:.6f}_to_{end_lat:.6f}_{end_lon:.6f}"
        return CACHE_DIR / f"route_{cache_key}.json"

    def _load_from_cache(self, cache_path: Path) -> Optional[Dict]:
        """Carga ruta desde caché."""
        if not ENABLE_CACHE or not cache_path.exists():
            return None
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                print(f" Cache HIT: {cache_path.name}")
                return data
        except Exception as e:
            print(f" Cache read error: {e}")
            return None

    def _save_to_cache(self, cache_path: Path, data: Dict) -> None:
        """Guarda ruta en caché."""
        if not ENABLE_CACHE:
            return
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
            print(f" Saved to cache: {cache_path.name}")
        except Exception as e:
            print(f" Cache write error: {e}")

    def get_route(self, start_lat: float, start_lon: float,
                  end_lat: float, end_lon: float) -> Dict:
        """
        Obtiene ruta real usando OpenRouteService.
        
        Returns:
            {
                "success": bool,
                "distance_km": float,
                "duration_min": float,
                "geometry": [[lon, lat], ...],
                "error": str (si falla)
            }
        """
        # 1. Verificar caché
        cache_path = self._get_cache_path(start_lat, start_lon, end_lat, end_lon)
        cached = self._load_from_cache(cache_path)
        if cached:
            return cached

        # 2. Preparar petición ORS
        coordinates = [[start_lon, start_lat], [end_lon, end_lat]]
        
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        body = {
            "coordinates": coordinates,
            "radiuses": [1000, 1000],
        }

        print(f"\n ORS REQUEST")
        print(f"    From: ({start_lat:.4f}, {start_lon:.4f})")
        print(f"    To:   ({end_lat:.4f}, {end_lon:.4f})")
        print(f"    Endpoint: {self.endpoint}")

        # 3. Intentar con reintentos
        for attempt in range(self.max_retries):
            try:
                print(f"    Attempt {attempt + 1}/{self.max_retries}...")
                
                response = requests.post(
                    self.endpoint,
                    json=body,
                    headers=headers,
                    timeout=self.timeout,
                )

                print(f"    Status: {response.status_code}")

                # Éxito
                if response.status_code == 200:
                    data = response.json()

                    # Parsear GeoJSON
                    if "features" in data and len(data["features"]) > 0:
                        feature = data["features"][0]
                        geometry = feature["geometry"]["coordinates"]
                        segments = feature["properties"].get("segments", [])
                        
                        if not segments:
                            print(f"    No segments in response")
                            continue

                        props = segments[0]
                        distance_km = props.get("distance", 0) / 1000.0
                        duration_min = props.get("duration", 0) / 60.0

                        result = {
                            "success": True,
                            "distance_km": round(distance_km, 2),
                            "duration_min": round(duration_min, 2),
                            "geometry": geometry,
                        }

                        print(f"    SUCCESS! Distance: {distance_km:.2f} km")
                        self._save_to_cache(cache_path, result)
                        return result

                # Rate limit
                elif response.status_code == 429:
                    print(f"    Rate limited, waiting...")
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue
                    else:
                        error_msg = "Rate limit exceeded"
                        print(f"    {error_msg}")
                        return {
                            "success": False,
                            "error": error_msg,
                            "distance_km": None,
                            "duration_min": None,
                        }

                # Otros errores
                else:
                    error_msg = f"API error {response.status_code}: {response.text[:200]}"
                    print(f"    {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "distance_km": None,
                        "duration_min": None,
                    }

            except requests.Timeout:
                print(f"    Timeout")
                if attempt < self.max_retries - 1:
                    continue
                return {
                    "success": False,
                    "error": "Request timeout",
                    "distance_km": None,
                    "duration_min": None,
                }

            except Exception as e:
                print(f"    Exception: {str(e)}")
                if attempt < self.max_retries - 1:
                    continue
                return {
                    "success": False,
                    "error": f"Unexpected error: {str(e)}",
                    "distance_km": None,
                    "duration_min": None,
                }

        # Si llegamos aquí, todos los intentos fallaron
        print(f"    Max retries exceeded")
        return {
            "success": False,
            "error": "Max retries exceeded",
            "distance_km": None,
            "duration_min": None,
        }


# ============================================
# INSTANCIA GLOBAL (singleton)
# ============================================
_ors_service = None

def get_ors_service() -> ORSService:
    """Devuelve instancia única del servicio ORS."""
    global _ors_service
    if _ors_service is None:
        _ors_service = ORSService()
    return _ors_service