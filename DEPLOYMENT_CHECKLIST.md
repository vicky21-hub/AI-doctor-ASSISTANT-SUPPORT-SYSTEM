# AI Doctor Support - Deployment Checklist

## Pre-Deployment Verification (72 Hours Before)

### Code Quality
- [ ] Run all tests: `pytest backend/`
- [ ] Check test coverage: `coverage report`
  - Target: >= 80% coverage
- [ ] Code linting: `pylint backend/`
- [ ] Type checking: `mypy backend/`
- [ ] Security scan: `bandit -r backend/`

### Database
- [ ] Verify all 36 diseases have complete data
- [ ] Check no empty arrays/strings in JSON
- [ ] Validate JSON syntax: `python3 -m json.tool backend/knowledge/human_diseases.json`
- [ ] Backup current database

### Frontend
- [ ] Build frontend: `npm run build`
- [ ] Check build size is reasonable
- [ ] Test in production mode
- [ ] Test on mobile browsers
- [ ] Check responsive design

### Backend
- [ ] Update requirements.txt
- [ ] Verify all imports work
- [ ] Check API endpoints respond
- [ ] Verify error handling
- [ ] Check logging configured

---

## Day of Deployment

### Morning Checklist (4 Hours Before)

**Code Verification**
- [ ] Latest code pulled from main branch
- [ ] No uncommitted changes
- [ ] All tests passing (green CI/CD)
- [ ] No failed linting checks
- [ ] Security scan clean

**Infrastructure**
- [ ] Database backup created
- [ ] Rollback plan documented
- [ ] Server resources available
  - [ ] Memory: 2GB+ available
  - [ ] Disk: 10GB+ free
  - [ ] CPU: Not above 70% baseline

**Documentation**
- [ ] Release notes prepared
- [ ] User guide updated
- [ ] API documentation current
- [ ] Change log updated

### 1 Hour Before Deployment

**Final Checks**
- [ ] All team members notified
- [ ] Customer support briefed
- [ ] Monitoring systems ready
- [ ] Rollback procedures tested
- [ ] Backup verified and testable

**Communication**
- [ ] Maintenance window announced (if needed)
- [ ] Status page updated
- [ ] Customer notifications sent
- [ ] Support team on standby

### Deployment Steps

**Step 1: Backup (5 minutes)**
```bash
# Backup database
mysqldump -u user -p dbname > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup application
tar -czf app_backup_$(date +%Y%m%d_%H%M%S).tar.gz /app/
```

**Step 2: Update Code (10 minutes)**
```bash
cd /app
git pull origin main
git log --oneline -5  # Verify commits

# Tag release
git tag -a v1.0-prod -m "Production release"
git push origin v1.0-prod
```

**Step 3: Install Dependencies (5 minutes)**
```bash
pip install -r backend/requirements.txt
npm install --production
npm run build
```

**Step 4: Verify Configuration (2 minutes)**
```bash
# Check environment variables
env | grep FLASK
env | grep DATABASE

# Test database connection
python3 backend/database/health_db.py test
```

**Step 5: Start Services (5 minutes)**
```bash
# Stop old services
systemctl stop ai-doctor-backend
systemctl stop ai-doctor-frontend

# Start new services
systemctl start ai-doctor-backend
systemctl start ai-doctor-frontend

# Verify services running
systemctl status ai-doctor-backend
systemctl status ai-doctor-frontend
```

**Step 6: Health Checks (5 minutes)**
```bash
# Check backend API
curl http://localhost:5000/health

# Check frontend
curl http://localhost:3000/

# Check database connection
curl http://localhost:5000/api/diseases/count
```

**Step 7: Smoke Tests (15 minutes)**
```bash
# Run smoke tests
pytest backend/tests/smoke_tests.py

# Check critical endpoints:
# POST /api/chat - Chat endpoint
# GET /api/diseases - Disease list
# POST /api/predict - Disease prediction
# POST /api/analyze - Report generation
```

---

## Post-Deployment (First 24 Hours)

### Immediate (0-1 Hour)

- [ ] Monitor error logs: `tail -f /var/log/ai-doctor/error.log`
- [ ] Check system resources
  - [ ] Memory usage normal
  - [ ] CPU usage normal
  - [ ] Disk space adequate
- [ ] Monitor error rate (should be < 1%)
- [ ] Check response times (should be < 2s)
- [ ] Verify no critical errors

### First 4 Hours

- [ ] Monitor user activity
- [ ] Check bug reports
- [ ] Verify analytics data
- [ ] Monitor database performance
- [ ] Check API response times

### First 24 Hours

- [ ] Comprehensive testing in production
  - [ ] Test symptom recognition
  - [ ] Test disease prediction
  - [ ] Test report generation
  - [ ] Test all 36 diseases
- [ ] User feedback monitoring
- [ ] Performance analysis
- [ ] Database query analysis

### Daily Monitoring (Ongoing)

```
Metrics to Track:
- API response time (avg, p95, p99)
- Error rate (should be < 0.5%)
- CPU usage (should be < 70%)
- Memory usage (should be < 80%)
- Database query time (avg < 200ms)
- User session duration
- Chart predictions accuracy
```

---

## Rollback Plan

### If Issues Occur

**Immediate Rollback (within 1 hour)**
```bash
# Stop current version
systemctl stop ai-doctor-backend
systemctl stop ai-doctor-frontend

# Restore from backup
tar -xzf app_backup_YYYYMMDD_HHMMSS.tar.gz -C /app

# Restore database
mysql -u user -p dbname < backup_YYYYMMDD_HHMMSS.sql

# Start previous version
systemctl start ai-doctor-backend
systemctl start ai-doctor-frontend

# Verify
curl http://localhost:5000/health
```

### Rollback Criteria

Initiate rollback immediately if:
- [ ] API response time > 5s
- [ ] Error rate > 5%
- [ ] Database corrupted/inaccessible
- [ ] Security vulnerability detected
- [ ] Data loss detected
- [ ] Any critical feature broken

---

## Configuration Checklist

### Environment Variables

```bash
# Flask
FLASK_ENV=production
FLASK_APP=backend/app.py
SECRET_KEY=<random-secret-key>

# Database
DB_HOST=localhost
DB_USER=ai_doctor
DB_PASSWORD=<secure-password>
DB_NAME=ai_doctor_db

# API
API_PORT=5000
API_HOST=0.0.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ai-doctor/app.log

# Frontend
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_ENV=production
```

### File Permissions

```bash
# Ensure correct permissions
chmod 750 /app/backend
chmod 750 /app/src
chmod 640 /app/backend/knowledge/human_diseases.json

# Log directory
mkdir -p /var/log/ai-doctor
chmod 755 /var/log/ai-doctor
```

### Service Configuration

Create `/etc/systemd/system/ai-doctor-backend.service`:
```ini
[Unit]
Description=AI Doctor Backend Service
After=network.target

[Service]
Type=simple
User=ai-doctor
WorkingDirectory=/app/backend
ExecStart=/usr/bin/python3 -m flask run --host=0.0.0.0
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

---

## Post-Deployment Validation

### API Health Check
```bash
#!/bin/bash

# Health endpoint
if curl -f http://localhost:5000/health > /dev/null; then
    echo "✓ Backend health check passed"
else
    echo "✗ Backend health check failed"
    exit 1
fi

# Test disease retrieval
if curl -f http://localhost:5000/api/diseases | grep -q "Dengue"; then
    echo "✓ Disease database accessible"
else
    echo "✗ Disease database check failed"
    exit 1
fi

# Test prediction
RESULT=$(curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"symptoms":["fever","cough"]}')

if echo $RESULT | grep -q "confidence"; then
    echo "✓ Prediction engine working"
else
    echo "✗ Prediction engine check failed"
    exit 1
fi

echo "All checks passed!"
```

---

## Success Criteria

### Green Light for Production

- [ ] 0 critical issues
- [ ] 0 blocking issues
- [ ] < 5 non-critical issues
- [ ] API response time < 2s (p99)
- [ ] Error rate < 0.5%
- [ ] All health checks passing
- [ ] Load test: 100+ concurrent users OK
- [ ] Security scan: 0 vulnerabilities
- [ ] User acceptance testing: PASSED

### Go-Live Decision

**Go**: If all success criteria met

**Hold**: If any critical item failing

**Rollback**: If production issues critical

---

## Sign-Off

- [ ] Development Lead: _________________ Date: _______
- [ ] QA Lead: _________________ Date: _______
- [ ] DevOps Lead: _________________ Date: _______
- [ ] Product Manager: _________________ Date: _______

---

## Post-Launch Retrospective (48 Hours After)

- [ ] Review deployment process
- [ ] Document lessons learned
- [ ] Identify improvement areas
- [ ] Plan for next deployment
- [ ] Update playbooks based on experience

---

**Deployment Owner**: [Name]  
**Deployment Date**: [Date]  
**Production URL**: [URL]  
**Support Contact**: [Contact]  
**Escalation**: [Escalation Protocol]

