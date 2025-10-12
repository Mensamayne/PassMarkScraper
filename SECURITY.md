# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

---

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please follow these steps:

### 🔒 Private Disclosure

**DO NOT** open a public issue for security vulnerabilities.

Instead:
1. Email the maintainers (if email provided)
2. Use GitHub Security Advisories (if available)
3. Open a private vulnerability report

### 📝 What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### ⏱️ Response Time

- Initial response: Within 48 hours
- Fix timeline: Depends on severity
  - Critical: Within 7 days
  - High: Within 14 days
  - Medium: Within 30 days
  - Low: Next release

---

## Security Best Practices

### For Users

1. **Keep dependencies updated**
   ```bash
   pip install -U -r requirements.txt
   ```

2. **Use Docker for isolation**
   ```bash
   docker-compose up -d
   ```

3. **Don't expose API publicly** without authentication
   - Use reverse proxy (nginx)
   - Add API key authentication
   - Use HTTPS

4. **Regular backups**
   ```bash
   curl -X POST http://localhost:9091/backup/create
   ```

5. **Monitor logs**
   ```bash
   tail -f logs/app.log
   ```

### For Developers

1. **Validate all user inputs**
2. **Use parameterized SQL queries** (already done with SQLite)
3. **Don't log sensitive data**
4. **Keep secrets in environment variables**
5. **Update dependencies regularly**

---

## Known Security Considerations

### Data Source
- Data is scraped from PassMark (public website)
- No authentication required for PassMark access
- Rate limiting recommended to avoid IP bans

### API Security
- **Default:** No authentication (local use only)
- **Recommended:** Add API key auth for production
- **CORS:** Enabled for all origins (change for production)

### Database
- SQLite file-based (no network exposure)
- No default credentials
- Read/write access via API only

---

## Security Checklist for Production

- [ ] Add API authentication (API keys, OAuth)
- [ ] Disable CORS or restrict to specific origins
- [ ] Use HTTPS with reverse proxy
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Regular security updates
- [ ] Backup encryption
- [ ] Log rotation and monitoring
- [ ] Container security scanning
- [ ] Network isolation

---

## Disclosure Policy

We follow **responsible disclosure**:

1. Report received
2. Vulnerability confirmed
3. Fix developed
4. Fix tested
5. Security advisory published
6. Fix released
7. Public disclosure (after fix deployed)

---

**Last Updated:** 2025-10-12

