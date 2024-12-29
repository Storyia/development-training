import time
from enum import Enum
from typing import Optional, Dict

from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel, Field

app = FastAPI()


class DogType(str, Enum):
    """
    Породы собак.
    """

    terrier = "terrier"
    bulldog = "bulldog"
    dalmatian = "dalmatian"


class Dog(BaseModel):
    """
    Модель собаки.
    """

    pk: Optional[int] = Field(None, title="Идентификатор")
    name: str = Field(..., title="Имя собаки")
    kind: DogType = Field(..., title="Порода собаки")
    age: Optional[int] = Field(None, title="Возраст собаки", ge=0)
    owner: Optional[str] = Field(None, title="Имя владельца")
    vaccinated: bool = Field(False, title="Привит ли")


class Timestamp(BaseModel):
    """
    Timestamp-модель.
    """

    id: int = Field(..., title="Идентификатор")
    timestamp: int = Field(..., title="Дата и время")


# база данных собак
DB_DOGS = {}


@app.get("/", response_model=list[Dog])
def root() -> list[Dog]:
    """
    Путь "GET /".

    Загрузка списка собак.

    :return:
    """

    return list(DB_DOGS.values())


@app.post("/post", response_model=Timestamp)
def get_post() -> Timestamp:
    """
    Путь "POST /post".

    :return:
    """

    return Timestamp(id=0, timestamp=time.time(),)


@app.get("/dog", response_model=list[Dog])
def get_dogs(kind: DogType = Query(..., title="Порода собаки")) -> list[Dog]:
    """
    Получение списка собак с фильтрацией по переданной породе собаки.

    :param kind: Порода собаки.
    :return:
    """

    # получение собак с фильтрацией по породе
    return [dog for dog in DB_DOGS.values() if dog.kind == kind]


@app.post("/dog", response_model=Dog)
def create_dog(dog: Dog) -> Dog:
    """
    Запись собак.

    :param dog: Объект собаки.
    :return:
    """

    pk = dog.pk
    if not pk:
        if DB_DOGS:
            pk = max(dog.pk for dog in DB_DOGS.values()) + 1
        else:
            pk = 1

    DB_DOGS[pk] = Dog(
        pk=pk,
        name=dog.name,
        kind=dog.kind,
        age=dog.age,
        owner=dog.owner,
        vaccinated=dog.vaccinated,
    )

    return DB_DOGS[pk]

@app.get("/dog/search", response_model=list[Dog])
def search_dog_by_name(name: str = Query(..., title="Имя собаки")) -> list[Dog]:
    """
    Поиск собак по имени.

    :param name: Имя собаки.
    :return: Список собак с совпадающим именем.
    """
    result = [dog for dog in DB_DOGS.values() if dog.name.lower() == name.lower()]
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Собаки с таким именем не найдены."
        )
    return result

@app.get("/dog/{pk}", response_model=Dog)
def get_dog_by_pk(pk: int) -> Optional[Dog]:
    """
    Получение собаки по идентификатору.

    :param pk: Идентификатор.
    :return:
    """

    if dog := DB_DOGS.get(pk):
        return dog

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Объект не найден."
    )


@app.patch("/dog/{pk}", response_model=Dog)
def update_dog(pk: int, update_data: Dict[str, Optional[str]]) -> Dog:
    """
    Обновление собаки по идентификатору.

    :param pk: Идентификатор.
    :param update_data: Словарь с полями для обновления.
    :return: Обновлённые данные собаки.
    """

    if pk not in DB_DOGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Собака с таким идентификатором не найдена.",
        )

    current_dog = DB_DOGS[pk]

    # Проверяем переданные поля
    invalid_keys = [key for key in update_data.keys() if not hasattr(current_dog, key)]
    if invalid_keys:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недопустимые поля: {', '.join(invalid_keys)}"
        )

    # Обновляем только переданные поля
    for key, value in update_data.items():
        if hasattr(current_dog, key) and value is not None:
            setattr(current_dog, key, value)

    DB_DOGS[pk] = current_dog

    return current_dog
@app.delete("/dog/{pk}", response_model=Dog)
def delete_dog(pk: int) -> Dog:
    """
    Удаление собаки по идентификатору.

    :param pk: Идентификатор собаки.
    :return: Удалённая собака.
    """
    if pk not in DB_DOGS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Собака с таким идентификатором не найдена.",
        )

    # Удаление собаки из базы данных
    deleted_dog = DB_DOGS.pop(pk)

    return deleted_dog