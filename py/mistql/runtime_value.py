from enum import Enum
from typing import Callable, List
import json


class RuntimeValueType(Enum):
    """
    Enumeration of the different types of runtime values available in MistQL
    """

    Null = "null"
    Boolean = "boolean"
    Number = "number"
    String = "string"
    Object = "object"
    Array = "array"
    Function = "function"
    Regex = "regex"


class RuntimeValue:
    @staticmethod
    def of(value):
        """
        Convert a Python value into a MistQL RuntimeValue
        """
        if isinstance(value, RuntimeValue):
            return value
        elif value is None:
            return RuntimeValue(RuntimeValueType.Null)
        elif isinstance(value, bool):
            return RuntimeValue(RuntimeValueType.Boolean, value)
        elif isinstance(value, int):
            return RuntimeValue(RuntimeValueType.Number, float(value))
        elif isinstance(value, float):
            return RuntimeValue(RuntimeValueType.Number, value)
        elif isinstance(value, str):
            return RuntimeValue(RuntimeValueType.String, value)
        elif isinstance(value, list):
            return RuntimeValue(
                RuntimeValueType.Array,
                [RuntimeValue.of(item) for item in value],
            )
        elif isinstance(value, dict):
            return RuntimeValue(
                RuntimeValueType.Object,
                {key: RuntimeValue.of(value[key]) for key in value},
            )
        else:
            raise ValueError(
                "Cannot convert external type to MistQL type: " + str(type(value))
            )

    @staticmethod
    def create_function(definition: Callable):
        """
        Create a new function that can be used in MistQL expressions
        """
        return RuntimeValue(
            RuntimeValueType.Function,
            definition,
        )

    @staticmethod
    def eq(a, b):
        if a.type != b.type:
            return False
        if a.type == RuntimeValueType.Null:
            return True
        elif a.type == RuntimeValueType.Boolean:
            return a.value == b.value
        elif a.type == RuntimeValueType.Number:
            return a.value == b.value
        elif a.type == RuntimeValueType.String:
            return a.value == b.value
        elif a.type == RuntimeValueType.Array:
            if len(a.value) != len(b.value):
                return False
            for i in range(len(a.value)):
                if not RuntimeValue.eq(a.value[i], b.value[i]):
                    return False
            return True
        elif a.type == RuntimeValueType.Object:
            if len(a.value) != len(b.value):
                return False
            for key, value in a.value.items():
                if key not in b.value:
                    return False
                if not RuntimeValue.eq(value, b.value[key]):
                    return False
            return True
        elif a.type == RuntimeValueType.Regex:
            return a.value.pattern == b.value.pattern and a.value.flags == b.value.flags
        elif a.type == RuntimeValueType.Function:
            # referential equality
            return a.value == b.value
        else:
            raise ValueError("Equality not yet implemented: " + str(a.type))

    def __init__(self, type, value=None):
        self.type = type
        self.value = value

    def to_python(self):
        """
        Convert a MistQL RuntimeValue into a Python value
        """
        if self.type == RuntimeValueType.Null:
            return None
        elif self.type == RuntimeValueType.Boolean:
            return self.value
        elif self.type == RuntimeValueType.Number:
            return self.value
        elif self.type == RuntimeValueType.String:
            return self.value
        elif self.type == RuntimeValueType.Array:
            return [item.to_python() for item in self.value]
        elif self.type == RuntimeValueType.Object:
            return {key: value.to_python() for key, value in self.value.items()}
        else:
            raise ValueError(
                "Cannot convert MistQL value type to Python: " + str(self.type)
            )

    def truthy(self) -> bool:
        """
        Return whether this value is truthy
        """
        if self.type == RuntimeValueType.Null:
            return False
        elif self.type == RuntimeValueType.Boolean:
            return self.value
        elif self.type == RuntimeValueType.Number:
            return bool(self.value)
        elif self.type == RuntimeValueType.String:
            return self.value != ""
        elif self.type == RuntimeValueType.Array:
            return len(self.value) > 0
        elif self.type == RuntimeValueType.Object:
            return len(self.value) > 0
        elif self.type == RuntimeValueType.Function:
            return True
        elif self.type == RuntimeValueType.Regex:
            return True
        else:
            raise ValueError("Truthiness not yet implemented: " + str(self.type))

    def to_json(self) -> str:
        """
        Convert this value to JSON string
        """
        return json.dumps(self.to_python())

    def to_string(self) -> str:
        """
        Convert this value to a string
        """
        if self.type == RuntimeValueType.String:
            return self.value
        else:
            return self.to_json()

    def to_float(self) -> float:
        if self.type == RuntimeValueType.Number:
            return self.value
        elif self.type == RuntimeValueType.String:
            return float(self.value)
        elif self.type == RuntimeValueType.Boolean:
            return float(self.value)
        elif self.type == RuntimeValueType.Null:
            return float(0)
        else:
            return float("nan")

    def __repr__(self) -> str:
        if self.type == RuntimeValueType.Function:
            return "<mistql [function]>"
        if self.type == RuntimeValueType.Regex:
            return "<mistql [regex]>"
        return f"<mistql {self.to_string()}>"

    def keys(self):
        if self.type == RuntimeValueType.Object:
            return [key for key in self.value]
        else:
            return []

    def access(self, string):
        """
        Access a property of this value
        """
        if self.type == RuntimeValueType.Object:
            if string in self.value:
                return self.value[string]
            else:
                return RuntimeValue(RuntimeValueType.Null)
        else:
            return None