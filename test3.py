from dataclasses import dataclass


@dataclass
class Employee:
    name: str
    dept: str
    salary: int


print(Employee())
