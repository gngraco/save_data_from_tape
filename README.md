# save_data_from_tape

Script docker para ler dados do [Tape](https://get.tapeapp.com) e criar tabelas e populá-las para cada aplicativo mapeado.

## Deploy

No diretório raiz execute:

`docker-compose up -d`

## Variáveis de ambiente

Exemplo de conteúdo do arquivo `.env` localizado na raiz:

```shell
TAPE_API_ENVFILE={credenciais_tape_filepath}
DATABASE_ENVFILE={credenciais_banco_dados_filepath}
MISC_ENVFILE={misc_env_filepath}
```

Exemplo de conteúdo do `TAPE_API_ENVFILE`:

```shell
# Tape Credenciais
TAPE_USER_KEY={user_key}

# Tape Apps IDs
# Workspace 1 - App 1 -> 12345
# Workspace 1 - App 2 -> 67890
# Workspace 2 - App 1 -> 98765
TAPE_APPS_IDS=12345,67890,98765
```

Exemplo de conteúdo do `DATABASE_ENVFILE`:

```shell
# Datalake
POSTGRES_HOST={host}
POSTGRES_PORT={port}
POSTGRES_USERNAME={username}
POSTGRES_PASSWORD={password}
POSTGRES_DATABASE={database}
```

Exemplo de conteúdo do `MISC_ENVFILE`:

```shell
# Times
TIMEOFFSET=7200
TIMEZONE_OFFSET=-3
```
