# Tunix IA

Assistente de estudos focado em Linux, terminal, distros e administracao de sistemas.

## O que a Tunix IA responde

- Comandos de terminal e navegacao no sistema
- Diferencas entre Ubuntu, Debian, Fedora, Arch, Mint e outras distros
- Instalacao, WSL, maquinas virtuais e dual boot
- Gerenciadores de pacotes como apt, dnf e pacman
- Permissoes, usuarios, grupos, sudo, chmod e chown
- systemd, logs, redes, SSH, firewall e servidores
- Bash, pipes, redirecionamento, scripts e cron

## Estrutura

- `index.html`, `styles.css`, `index.js`: interface do chat
- `server.py`: backend Flask, rotas e memoria
- `ollama.py`: integracao com Ollama/Ollama Cloud
- `roadmap.html`: trilha de estudos Linux
- `supabase_schema.sql`: tabelas para usuarios, conversas e mensagens
- `vercel.json`: configuracao de deploy na Vercel

## Autenticacao e acesso unico

A Tunix IA usa Supabase Auth. Cada pessoa entra com email/senha ou GitHub e recebe um `user_id` unico. O backend valida o token do usuario antes de liberar conversas, historico e chat.

As conversas ficam salvas no Supabase, separadas por usuario:

- `tunix_conversations`
- `tunix_messages`

Execute o conteudo de `supabase_schema.sql` no SQL Editor do Supabase antes de publicar.

## Deploy na Vercel

Configure as variaveis de ambiente:

```txt
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua_anon_key
SUPABASE_SERVICE_ROLE_KEY=sua_service_role_key
OLLAMA_API_KEY=sua_chave_da_ollama
OLLAMA_MODEL=minimax-m2.5:cloud
```

No Vercel, nao use `http://localhost:11434/api/chat` como `OLLAMA_URL`. O backend precisa chamar um endpoint publico, como `https://ollama.com/api/chat`.

Para login com GitHub, ative o provider GitHub no painel do Supabase em Authentication > Providers e configure a URL publicada da Vercel como redirect permitido.
