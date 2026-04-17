"""Admin notifications for AVISO (daily digest) and ALERTA (immediate).

Transports: Supabase realtime for dashboard updates, email/Slack webhook for ALERTA.
Never sends prompt content — only metadata and event ids.
"""
