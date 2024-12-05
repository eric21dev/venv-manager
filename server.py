import os
import subprocess
from pathlib import Path
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

def get_pyenv_root():
    """Obtiene el directorio raíz de pyenv."""
    try:
        pyenv_root = subprocess.check_output(["pyenv", "root"], text=True).strip()
        return Path(pyenv_root)
    except subprocess.CalledProcessError:
        return None

def list_pyenv_venvs():
    """Obtiene la lista de entornos virtuales de pyenv con sus tamaños y versiones."""
    pyenv_root = get_pyenv_root()
    if not pyenv_root:
        return []
    
    versions_dir = pyenv_root / "versions"
    if not versions_dir.exists():
        return []
    
    venvs = []
    for venv in versions_dir.iterdir():
        if venv.is_dir():
            python_bin = venv / "bin" / "python"
            if python_bin.exists():
                try:
                    version = subprocess.check_output(
                        [python_bin, "--version"], text=True
                    ).strip()
                except subprocess.CalledProcessError:
                    version = "Desconocida"
                
                size = sum(f.stat().st_size for f in venv.rglob('*') if f.is_file())
                size_mb = size / (1024 ** 2)
                
                venvs.append({
                    "name": venv.name,
                    "version": version,
                    "size": f"{size_mb:.2f} MB"
                })
    return venvs

@app.route("/")
def index():
    """Página principal."""
    venvs = list_pyenv_venvs()
    return render_template("index.html", venvs=venvs)

@app.route("/api/venvs")
def api_venvs():
    """Devuelve los entornos virtuales como JSON."""
    venvs = list_pyenv_venvs()
    return jsonify(venvs)

@app.route("/api/packages", methods=["POST"])
def list_packages():
    """Lista los paquetes instalados en un entorno virtual."""
    venv_name = request.form.get("venv_name")
    pyenv_root = get_pyenv_root()
    if not pyenv_root:
        return jsonify({"status": "error", "message": "Pyenv no configurado"}), 500

    python_bin = pyenv_root / "versions" / venv_name / "bin" / "pip"
    try:
        output = subprocess.check_output([python_bin, "list", "--format=json"], text=True)
        return jsonify({"status": "success", "packages": output})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/create_venv", methods=["POST"])
def create_venv():
    """Crea un nuevo entorno virtual."""
    pyenv_root = get_pyenv_root()
    venv_name = request.form.get("venv_name")
    python_version = request.form.get("python_version")
    try:
        subprocess.run(["pyenv", "virtualenv", python_version, venv_name], check=True)
        return jsonify({"status": "success", "message": f"Entorno {venv_name} creado con Python {python_version}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/delete_venv", methods=["POST"])
def delete_venv():
    """Elimina un entorno virtual."""
    pyenv_root = get_pyenv_root()
    venv_name = request.form.get("venv_name")
    versions_dir = pyenv_root / "versions"
    venv_path = versions_dir / venv_name

    if venv_path.exists():
        try:
            subprocess.run(["rm", "-rf", str(venv_path)], check=True)
            return jsonify({"status": "success", "message": f"Eliminado {venv_name}"})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        return jsonify({"status": "error", "message": f"{venv_name} no encontrado"}), 404

@app.route("/clone_venv", methods=["POST"])
def clone_venv():
    """Clona un entorno virtual existente."""
    pyenv_root = get_pyenv_root()
    source_venv = request.form.get("source_venv")
    target_venv = request.form.get("target_venv")
    try:
        subprocess.run(["cp", "-r", str(pyenv_root / "versions" / source_venv), str(pyenv_root / "versions" / target_venv)], check=True)
        return jsonify({"status": "success", "message": f"Clonado {source_venv} como {target_venv}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/export_venv", methods=["POST"])
def export_venv():
    """Exporta las dependencias de un entorno virtual."""
    pyenv_root = get_pyenv_root()
    venv_name = request.form.get("venv_name")
    requirements_path = Path(f"{venv_name}_requirements.txt")
    python_bin = pyenv_root / "versions" / venv_name / "bin" / "pip"
    try:
        subprocess.run([python_bin, "freeze"], stdout=requirements_path.open("w"), check=True)
        return jsonify({"status": "success", "message": f"Exportado a {requirements_path}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/import_venv", methods=["POST"])
def import_venv():
    """Importa dependencias a un entorno virtual."""
    pyenv_root = get_pyenv_root()
    venv_name = request.form.get("venv_name")
    requirements_file = request.form.get("requirements_file")
    python_bin = pyenv_root / "versions" / venv_name / "bin" / "pip"
    try:
        subprocess.run([python_bin, "install", "-r", requirements_file], check=True)
        return jsonify({"status": "success", "message": f"Dependencias importadas a {venv_name}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)