# Production Readiness Checklist

Run this command before declaring any system "production-ready".

## Usage
```
/command-invoke production-checklist
```

## Checklist

### 1. Functionality ✅
- [ ] All planned features implemented
- [ ] All user stories tested manually
- [ ] Edge cases handled
- [ ] Error messages user-friendly
- [ ] Performance acceptable (< 3s response times)

### 2. Testing 🧪
- [ ] Unit test coverage ≥ 90%
- [ ] All unit tests passing (100%)
- [ ] Integration tests implemented
- [ ] Integration tests passing (100%)
- [ ] E2E tests for critical paths
- [ ] E2E tests passing (100%)
- [ ] Load testing completed (2x expected traffic)
- [ ] No flaky tests

### 3. Security 🔒
- [ ] Rate limiting implemented (API and webhooks)
- [ ] Input validation (all endpoints)
- [ ] Output encoding (prevent XSS)
- [ ] Authentication implemented
- [ ] Authorization checks working
- [ ] Webhook signature verification
- [ ] Audit logging for state changes
- [ ] Secret management (no hardcoded keys)
- [ ] HTTPS enforced
- [ ] Security scan passed
- [ ] IP filtering configured (webhooks)
- [ ] Token rotation support

### 4. Operations 🔧
- [ ] Health check endpoints (`/health`, `/health/db`, `/health/ready`)
- [ ] Metrics collection (Prometheus or equivalent)
- [ ] Logging structured (JSON format)
- [ ] Error tracking (Sentry or equivalent)
- [ ] Deployment automated
- [ ] Rollback procedure tested
- [ ] Backup strategy implemented
- [ ] Database migrations tested
- [ ] Monitoring dashboards created
- [ ] Alerting configured
- [ ] On-call rotation defined
- [ ] Incident response plan documented

### 5. Performance ⚡
- [ ] Load tested (2x expected traffic)
- [ ] Database queries optimized
- [ ] Connection pooling configured
- [ ] Caching strategy implemented
- [ ] Response times acceptable (< 3s for p95)
- [ ] Resource limits defined (CPU, memory)
- [ ] Auto-scaling configured (if applicable)

### 6. Documentation 📚
- [ ] README complete with quick start
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Architecture diagrams updated
- [ ] Deployment guide written
- [ ] Operations runbook created
- [ ] Troubleshooting guide included
- [ ] User guide available
- [ ] Changelog maintained
- [ ] Environment variables documented

### 7. Database 💾
- [ ] Migrations tested (up and down)
- [ ] Backup automated
- [ ] Restore tested
- [ ] Connection pooling optimized
- [ ] Indexes on foreign keys
- [ ] Slow query monitoring
- [ ] Database credentials rotated

### 8. Compliance 📋
- [ ] License file present
- [ ] Dependencies vetted (no vulnerabilities)
- [ ] Data privacy considered
- [ ] GDPR/compliance requirements met
- [ ] Terms of service defined
- [ ] Privacy policy created

### 9. Observability 👁️
- [ ] Request tracing enabled
- [ ] Error rate monitored
- [ ] Latency tracked (p50, p95, p99)
- [ ] Database performance monitored
- [ ] External service health tracked
- [ ] Custom business metrics defined

### 10. Resilience 💪
- [ ] Circuit breakers implemented
- [ ] Retry logic with exponential backoff
- [ ] Timeout handling
- [ ] Graceful degradation
- [ ] Rate limiting prevents cascading failures
- [ ] Dead letter queue for failed jobs

## Scoring

Count the checkmarks:

**50-54 ✅**: **Production Ready** ✅ - Ship it!
**45-49 ✅**: **Almost There** ⚠️ - Address critical gaps, then ship
**35-44 ✅**: **Not Ready** ❌ - Significant work remains
**< 35 ✅**: **Not Production Quality** ❌ - Major gaps exist

## Output Format

Generate a report showing:

1. **Total Score**: X/54 checkmarks
2. **Category Scores**:
   - Functionality: X/5
   - Testing: X/8
   - Security: X/12
   - Operations: X/12
   - Performance: X/7
   - Documentation: X/9
   - Database: X/7
   - Compliance: X/5
   - Observability: X/6
   - Resilience: X/6

3. **Missing Items** (by category):
   - List all unchecked items with recommendations

4. **Critical Gaps** (blockers):
   - Highlight must-fix items before deployment

5. **Estimated Effort**:
   - Time to reach production-ready (hours)

## Action Items

For each missing item:
- **Priority**: P0 (critical), P1 (important), P2 (nice-to-have)
- **Effort**: Hours to implement
- **Owner**: Who should fix it
- **Blocker**: Does this block deployment?

## Example Report

```markdown
# Production Readiness Report

**Date**: 2026-01-02
**Project**: Project Orchestrator
**Version**: 0.1.0

## Overall Score: 47/54 (87%) - Almost There ⚠️

### Category Scores
- ✅ Functionality: 5/5 (100%)
- ⚠️ Testing: 6/8 (75%)
- ✅ Security: 12/12 (100%)
- ⚠️ Operations: 10/12 (83%)
- ✅ Performance: 7/7 (100%)
- ✅ Documentation: 9/9 (100%)
- ⚠️ Database: 5/7 (71%)
- ✅ Compliance: 5/5 (100%)
- ⚠️ Observability: 4/6 (67%)
- ✅ Resilience: 6/6 (100%)

### Critical Gaps (Blockers)

**Testing**:
- ❌ E2E tests not implemented (P0, 4 hours)
- ❌ Load testing not completed (P0, 2 hours)

**Operations**:
- ❌ Monitoring dashboards not created (P1, 2 hours)
- ❌ Alerting not configured (P1, 1 hour)

**Database**:
- ❌ Restore not tested (P0, 1 hour)
- ❌ Database credentials not rotated (P2, 30 min)

**Observability**:
- ❌ Custom business metrics not defined (P2, 1 hour)
- ❌ Request tracing not enabled (P2, 2 hours)

### Recommendations

**Before Deployment** (P0 - 7 hours):
1. Implement E2E tests for critical user paths
2. Complete load testing at 2x expected traffic
3. Test database restore procedure

**Week 1 Post-Deployment** (P1 - 3 hours):
4. Create monitoring dashboards
5. Configure alerting rules

**Month 1** (P2 - 3.5 hours):
6. Rotate database credentials
7. Define custom business metrics
8. Enable request tracing

### Estimated Time to Production Ready: 7 hours (P0 items only)

### Deployment Recommendation: ⚠️ Fix P0 items first (7 hours), then deploy
```

## Best Practices

1. **Run before every major release**
2. **Track trends over time** (are we improving?)
3. **Be honest** - don't check boxes that aren't truly complete
4. **Prioritize ruthlessly** - not everything is P0
5. **Share with team** - transparency builds trust

## Notes

- This checklist is comprehensive but may not apply to all projects
- Adjust based on your specific requirements
- Add project-specific checks as needed
- Review and update checklist regularly

---

**Remember**: Production readiness is not binary. It's a spectrum from "demo" to "enterprise-grade". Be honest about where you are, and plan to get where you need to be.

**The goal is not to check all boxes. The goal is to ship confidently.**
