create table
  public.global_inventory (
    id bigint generated by default as identity,
    num_red_ml integer not null default 0,
    gold integer not null default 100,
    num_blue_ml integer not null default 0,
    num_green_ml integer not null default 0,
    num_dark_ml integer not null default 0,
    constraint global_inventory_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.catalog (
    id bigint generated by default as identity,
    sku text not null default 'NULL'::text,
    name text not null default 'NULL'::text,
    quantity integer not null default 0,
    price integer not null default 0,
    potion_type integer[] not null default '{0,0,0,0}'::integer[],
    constraint catalog_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.carts (
    id bigint generated by default as identity,
    customer_name text not null,
    payment text null,
    created_at timestamp with time zone not null default now(),
    constraint carts_pkey primary key (id)
  ) tablespace pg_default;

create table
  public.cart_items (
    cart_id bigint generated by default as identity,
    catalog_id bigint not null,
    quantity integer not null,
    constraint cart_items_cart_id_fkey foreign key (cart_id) references carts (id),
    constraint cart_items_catalog_id_fkey foreign key (catalog_id) references catalog (id)
  ) tablespace pg_default;