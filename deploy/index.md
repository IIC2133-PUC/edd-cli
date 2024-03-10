# Deploy EDD Runner Server

Basado parte en esta guia: https://tutlinks.com/deploy-fastapi-on-ubuntu-gunicorn-caddy-2/

## Setup

- Clonar el CLI

  ```
  git clone https://github.com/IIC2133-PUC/edd-cli.git
  ```

- Instalar paquetes para Python

  ```sh
  sudo apt update
  sudo apt install libssl-dev libsqlite3-dev
  ```

- Instalar Python 3.12

  Usando via pyenv

  ```sh
  curl https://pyenv.run | bash
  pyenv install 3.12
  ```

- [OPCIONAL] Instalar UV para .venv y dependencias

  ```sh
  curl -LsSf https://astral.sh/uv/install.sh | sh
  uv venv
  uv pip install -r requirements.txt
  ```

- Setear https://gunicorn.org/

  ```sh
  uv pip install gunicorn
  ```

- Luego de añadir `guicorn.service`:

  ```sh
  # Comando a ejecutar
  gunicorn -k uvicorn.workers.UvicornWorker edd_cli.server:app
  ```

  ```sh
  sudo systemctl daemon-reload
  sudo systemctl enable gunicorn.service
  sudo systemctl start gunicorn.service

  # Para ver logs
  sudo systemctl status gunicorn.service
  ```

- Instalar
  https://caddyserver.com/docs/install

- Añadir el `Caddyfile`

  ```sh
  nano /etc/caddy/Caddyfile
  ```

- Reiniciar Caddy

  ```sh
  sudo systemctl restart caddy.service
  ```

## Actualizar el servidor

- Actualizar el servidor

  ```sh
  git pull
  ```

- Actualizar dependencias

  ```sh
  uv pip install -r requirements.txt
  ```

- Reiniciar el servidor

  ```sh
  sudo systemctl restart gunicorn.service
  ```
