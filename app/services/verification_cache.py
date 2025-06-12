import random
import string
import time
from typing import Optional, Dict
import threading

class VerificationCache:
    """
    Geçici doğrulama kodlarını bellekte saklar
    Thread-safe implementasyon
    """
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def generate_code(self, length: int = 6) -> str:
        """
        Rastgele doğrulama kodu oluşturur
        """
        return ''.join(random.choices(string.digits, k=length))
    
    def store_code(self, email: str, expire_minutes: int = 3, code_type: str = "verification") -> str:
        """
        E-posta için doğrulama kodu oluşturur ve saklar
        """
        code = self.generate_code()
        expire_time = time.time() + (expire_minutes * 60)
        
        cache_key = f"{code_type}_{email}"  # verification_email@example.com veya reset_email@example.com
        
        with self._lock:
            self._cache[cache_key] = {
                'code': code,
                'expire_time': expire_time,
                'attempts': 0,
                'max_attempts': 3,
                'type': code_type
            }
        
        return code
    
    def verify_code(self, email: str, input_code: str, code_type: str = "verification") -> bool:
        """
        Doğrulama kodunu kontrol eder
        """
        cache_key = f"{code_type}_{email}"
        
        with self._lock:
            if cache_key not in self._cache:
                return False
            
            cache_data = self._cache[cache_key]
            
            # Süre kontrolü
            if time.time() > cache_data['expire_time']:
                del self._cache[cache_key]
                return False
            
            # Deneme sayısı kontrolü
            if cache_data['attempts'] >= cache_data['max_attempts']:
                del self._cache[cache_key]
                return False
            
            # Kod kontrolü
            if cache_data['code'] == input_code:
                del self._cache[cache_key]  # Başarılı doğrulama sonrası sil
                return True
            else:
                cache_data['attempts'] += 1
                return False
    
    def get_remaining_time(self, email: str, code_type: str = "verification") -> Optional[int]:
        """
        Kodun kalan süresini saniye cinsinden döner
        """
        cache_key = f"{code_type}_{email}"
        
        with self._lock:
            if cache_key not in self._cache:
                return None
            
            cache_data = self._cache[cache_key]
            remaining = int(cache_data['expire_time'] - time.time())
            
            if remaining <= 0:
                del self._cache[cache_key]
                return None
            
            return remaining
    
    def cleanup_expired(self):
        """
        Süresi dolmuş kodları temizler
        """
        current_time = time.time()
        with self._lock:
            expired_emails = [
                email for email, data in self._cache.items()
                if current_time > data['expire_time']
            ]
            
            for email in expired_emails:
                del self._cache[email]
    
    def has_active_code(self, email: str, code_type: str = "verification") -> bool:
        """
        E-posta için aktif kod var mı kontrol eder
        """
        cache_key = f"{code_type}_{email}"
        
        with self._lock:
            if cache_key not in self._cache:
                return False
            
            if time.time() > self._cache[cache_key]['expire_time']:
                del self._cache[cache_key]
                return False
            
            return True

# Global instance
verification_cache = VerificationCache() 