import numpy as np
from django.db import models


class NDArrayField(models.BinaryField):  # For storing NumPy arrays as binary data
    description = "Хранит NumPy массив как сырые байты (float32)"

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        # Превращаем байты из SQLite обратно в NumPy
        return np.frombuffer(value, dtype=np.float32)

    def to_python(self, value):
        if isinstance(value, np.ndarray):
            return value
        if value is None:
            return value
        return np.frombuffer(value, dtype=np.float32)

    def get_prep_value(self, value):
        if value is None:
            return value
        if isinstance(value, np.ndarray):
            return value.astype(np.float32).tobytes()
        return value
