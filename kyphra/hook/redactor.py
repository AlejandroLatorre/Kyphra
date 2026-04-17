"""PII redaction applied BEFORE any external call.

Replaces identifiable data (emails, DNI, NIE, phones, IBANs, card numbers)
with structural tokens like <EMAIL>, <DNI>. The redactor is the only
sanctioned path from raw prompt to classifier client.
"""
