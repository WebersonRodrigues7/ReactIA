create table if not exists public.tunix_conversations (
  id text primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null default 'Nova conversa',
  message_count integer not null default 0,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.tunix_messages (
  id bigserial primary key,
  conversation_id text not null references public.tunix_conversations(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  role text not null check (role in ('user', 'assistant')),
  content text not null,
  created_at timestamptz not null default now()
);

create index if not exists tunix_conversations_user_updated_idx
  on public.tunix_conversations (user_id, updated_at desc);

create index if not exists tunix_messages_conversation_created_idx
  on public.tunix_messages (conversation_id, created_at asc);

alter table public.tunix_conversations enable row level security;
alter table public.tunix_messages enable row level security;

drop policy if exists "Users can read own conversations" on public.tunix_conversations;
create policy "Users can read own conversations"
  on public.tunix_conversations for select
  using (auth.uid() = user_id);

drop policy if exists "Users can read own messages" on public.tunix_messages;
create policy "Users can read own messages"
  on public.tunix_messages for select
  using (auth.uid() = user_id);
