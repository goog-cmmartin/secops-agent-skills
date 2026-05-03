# Google SecOps Agent Skills

A modular, version-controlled CLI tool designed to act as a "Skill Pack" for AI Agents interacting with Google SecOps (Chronicle) via the MCP API.

## Installation for OpenCode

To install this skill pack into your local OpenCode environment, simply run the installation script. This will automatically generate the Python virtual environment, install dependencies, and register the skills with OpenCode.

```bash
cd google-secops-skills
./install.sh
```

**Post-Installation:**
1. Ensure you have active Google Application Default Credentials: 
   ```bash
   gcloud auth application-default login
   ```
2. Edit the `.env` file that was generated in the repository root with your specific Google SecOps details:
   ```ini
   SECOPS_PROJECT_ID=your-gcp-project-id
   SECOPS_CUSTOMER_ID=your-chronicle-customer-uuid
   SECOPS_REGION=us
   ```

## Agent Usage
Once installed, OpenCode will automatically discover the `secops-router` skill. You can simply ask OpenCode: *"What can you do with Google SecOps?"* or ask it directly to perform a task like *"List my highest priority cases in Chronicle."*