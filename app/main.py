import os
from dotenv import load_dotenv
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from contextlib import asynccontextmanager

# --- CARGAR VARIABLES DE ENTORNO ---
# Esto leerá tu archivo .env para proteger tus credenciales de AWS
load_dotenv()

# --- CONFIGURACIÓN DE BASE DE DATOS ---
DATABASE_URL = os.getenv("DATABASE_URL")

# Validación por si el archivo .env no existe o está mal configurado
if not DATABASE_URL:
    raise ValueError("¡Error! La variable DATABASE_URL no está configurada. Asegúrate de crear el archivo .env")

engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

# --- MODELOS DE DATOS ---
# Entidad 1: Libro
class LibroBase(SQLModel):
    titulo: str
    autor: str
    descripcion: Optional[str] = None
    anio_publicacion: int

class Libro(LibroBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class LibroCreate(LibroBase):
    pass

class LibroUpdate(SQLModel):
    titulo: Optional[str] = None
    autor: Optional[str] = None
    descripcion: Optional[str] = None
    anio_publicacion: Optional[int] = None

# Entidad 2: Usuario
class UsuarioBase(SQLModel):
    nombre: str
    email: str = Field(unique=True, index=True)
    edad: int

class Usuario(UsuarioBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioUpdate(SQLModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    edad: Optional[int] = None

# --- INICIALIZACIÓN DE APP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear las tablas en tu base de datos de PostgreSQL al iniciar
    SQLModel.metadata.create_all(engine)
    yield

app = FastAPI(
    title="API de Gestión de Biblioteca",
    description="API RESTful implementada con FastAPI y SQLModel para despliegue en AWS EC2 y RDS",
    version="1.0.0",
    lifespan=lifespan
)

# --- ENDPOINTS PARA LIBROS (CRUD) ---

@app.post("/libros/", response_model=Libro, status_code=201)
def crear_libro(libro: LibroCreate, session: Session = Depends(get_session)):
    db_libro = Libro.model_validate(libro)
    session.add(db_libro)
    session.commit()
    session.refresh(db_libro)
    return db_libro

@app.get("/libros/", response_model=List[Libro])
def leer_libros(session: Session = Depends(get_session)):
    libros = session.exec(select(Libro)).all()
    return libros

@app.get("/libros/{libro_id}", response_model=Libro)
def leer_libro(libro_id: int, session: Session = Depends(get_session)):
    libro = session.get(Libro, libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return libro

@app.put("/libros/{libro_id}", response_model=Libro)
def actualizar_libro(libro_id: int, libro_data: LibroUpdate, session: Session = Depends(get_session)):
    db_libro = session.get(Libro, libro_id)
    if not db_libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")

    data = libro_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_libro, key, value)

    session.add(db_libro)
    session.commit()
    session.refresh(db_libro)
    return db_libro

@app.delete("/libros/{libro_id}")
def eliminar_libro(libro_id: int, session: Session = Depends(get_session)):
    libro = session.get(Libro, libro_id)
    if not libro:
        raise HTTPException(status_code=404, detail="Libro no encontrado")
    session.delete(libro)
    session.commit()
    return {"ok": True, "message": f"Libro {libro_id} eliminado correctamente"}

# --- ENDPOINTS PARA USUARIOS (CRUD) ---

@app.post("/usuarios/", response_model=Usuario, status_code=201)
def crear_usuario(usuario: UsuarioCreate, session: Session = Depends(get_session)):
    db_usuario = Usuario.model_validate(usuario)
    session.add(db_usuario)
    session.commit()
    session.refresh(db_usuario)
    return db_usuario

@app.get("/usuarios/", response_model=List[Usuario])
def leer_usuarios(session: Session = Depends(get_session)):
    usuarios = session.exec(select(Usuario)).all()
    return usuarios

@app.get("/usuarios/{usuario_id}", response_model=Usuario)
def leer_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@app.put("/usuarios/{usuario_id}", response_model=Usuario)
def actualizar_usuario(usuario_id: int, usuario_data: UsuarioUpdate, session: Session = Depends(get_session)):
    db_usuario = session.get(Usuario, usuario_id)
    if not db_usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    data = usuario_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(db_usuario, key, value)

    session.add(db_usuario)
    session.commit()
    session.refresh(db_usuario)
    return db_usuario

@app.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int, session: Session = Depends(get_session)):
    usuario = session.get(Usuario, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    session.delete(usuario)
    session.commit()
    return {"ok": True, "message": f"Usuario {usuario_id} eliminado correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
