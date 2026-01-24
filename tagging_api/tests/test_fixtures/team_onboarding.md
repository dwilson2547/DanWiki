# New Team Member Onboarding

Welcome to the team! This guide will help you get up to speed quickly.

## First Day Checklist

- [ ] Complete HR paperwork
- [ ] Receive equipment (laptop, monitor, accessories)
- [ ] Set up email and communication accounts
- [ ] Meet your manager and team
- [ ] Get building access badge
- [ ] Review company handbook
- [ ] Set up development environment

## Week 1 Goals

### Access and Accounts

You'll need access to:

1. **GitHub**: Request org access from your manager
2. **Jira**: For task tracking
3. **Confluence**: Internal documentation
4. **Slack**: Team communication (#engineering, #general)
5. **AWS Console**: Production access (limited initially)
6. **VPN**: For remote access to internal services

### Development Environment

Follow our setup guide:

```bash
# Clone the main repository
git clone https://github.com/company/main-app.git
cd main-app

# Install dependencies
npm install
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your local settings

# Start services
docker-compose up -d
npm run dev
```

### Learn the Codebase

1. Read the README.md and architecture documentation
2. Run the test suite to ensure everything works
3. Build and run the application locally
4. Review the last 3 sprint retrospectives
5. Understand our git workflow (feature branches, PRs)

## Key Resources

### Documentation

- [Architecture Overview](../architecture/overview.md)
- [API Documentation](https://api-docs.company.com)
- [Coding Standards](../development/standards.md)
- [Testing Guidelines](../development/testing.md)

### Communication

**Daily Standups**: 9:30 AM in #standup channel
- What you did yesterday
- What you're doing today
- Any blockers

**Sprint Planning**: Every other Monday
**Retrospectives**: End of each sprint
**Demo Day**: Friday afternoons

### Development Workflow

1. Pick a task from the sprint backlog
2. Create feature branch: `feature/JIRA-123-description`
3. Write code and tests
4. Run linter and tests locally
5. Push and create Pull Request
6. Address review comments
7. Merge when approved and CI passes

### Getting Help

- **Technical questions**: Ask in #engineering
- **Process questions**: Ask your onboarding buddy
- **Urgent issues**: Ping your manager
- **General questions**: #help channel

Don't hesitate to ask questions! Everyone is here to help.

## Week 2-4 Goals

### Complete First Tasks

You'll be assigned some "good first issues":
- Bug fixes
- Documentation updates  - Small feature implementations
- Test coverage improvements

### Pair Programming Sessions

Schedule time with:
- Frontend lead (2 hours)
- Backend lead (2 hours)
- DevOps engineer (1 hour)
- QA engineer (1 hour)

### Review Key Systems

- Authentication and authorization
- Database schema and migrations
- API design patterns
- Frontend state management
- CI/CD pipeline
- Monitoring and logging

## Month 1 Goals

- Deploy your first feature to production
- Present in demo day
- Complete onboarding survey
- Schedule 1:1 with manager for feedback

## Learning Resources

### Recommended Reading

- "Clean Code" by Robert Martin
- "The Pragmatic Programmer" by Hunt & Thomas
- Our internal engineering blog

### Courses (Free Access)

- LinkedIn Learning: Team subscription
- Pluralsight: Company account
- Frontend Masters: Team plan

### Conferences

- Annual budget for 1-2 conferences per year
- Submit proposals 3 months in advance

## Team Culture

### Our Values

1. **Collaboration**: We win as a team
2. **Quality**: Take pride in your work
3. **Learning**: Grow continuously
4. **Transparency**: Communicate openly
5. **Balance**: Sustainable pace, not sprint

### Work-Life Balance

- Core hours: 10 AM - 4 PM
- Flexible schedule around core hours
- Remote work: 2 days/week after first month
- Unlimited PTO (with manager approval)
- No expectation to respond after hours

## Performance Expectations

### 30-day review

- Environment setup complete
- Deployed at least 1 feature/fix
- Comfortable with development workflow

### 90-day review

- Independently working on tasks
- Contributing to team discussions
- Understanding of system architecture
- Positive team collaboration

## Questions?

Reach out to:
- **Onboarding Buddy**: John Smith (@john)
- **Manager**: Jane Doe (@jane)
- **HR**: hr@company.com
