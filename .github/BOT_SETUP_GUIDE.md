# 🤖 Bot Setup Guide - Personal Access Token Configuration

## 🚨 **Why This Is Needed**

Your repository is under the **`Refactron-ai`** organization, which has workflow permissions set to **"Read repository contents and packages permissions"**. This restricts GitHub Actions from writing to issues/PRs.

**Solution:** Use a Personal Access Token (PAT) instead of the default `GITHUB_TOKEN`.

---

## 📋 **Step-by-Step Setup**

### **Step 1: Create a Personal Access Token**

1. **Go to GitHub Token Settings:**
   ```
   https://github.com/settings/tokens
   ```

2. **Click "Generate new token (classic)"**
   - Or click this direct link: https://github.com/settings/tokens/new

3. **Configure the token:**
   - **Note/Name:** `Refactron Bot Token`
   - **Expiration:** Choose your preference (recommend: `No expiration` or `1 year`)

4. **Select the following scopes:**
   - ✅ **`repo`** - Full control of private repositories
     - This gives access to:
       - `repo:status` - Commit status
       - `repo_deployment` - Deployment status
       - `public_repo` - Public repositories
       - `repo:invite` - Invitations
       - `security_events` - Security events
   - ✅ **`workflow`** - Update GitHub Action workflows
   - ✅ **`write:packages`** - Upload packages to GitHub Package Registry
   - ✅ **`read:org`** - Read org and team membership (optional but recommended)

5. **Click "Generate token"**

6. **🚨 IMPORTANT: Copy the token immediately!**
   - The token will look like: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
   - You won't be able to see it again
   - Save it temporarily in a secure location

---

### **Step 2: Add Token to Repository Secrets**

1. **Go to Repository Secrets:**
   ```
   https://github.com/Refactron-ai/Refactron_lib/settings/secrets/actions
   ```

2. **Click "New repository secret"**

3. **Configure the secret:**
   - **Name:** `BOT_TOKEN` (⚠️ Must be exactly this name!)
   - **Secret:** Paste the token you copied from Step 1

4. **Click "Add secret"**

5. **Verify:**
   - You should see `BOT_TOKEN` listed in "Repository secrets"
   - The value will be hidden (shown as `••••••••`)

---

### **Step 3: Test the Setup**

1. **Create a test issue:**
   ```
   https://github.com/Refactron-ai/Refactron_lib/issues/new
   ```

2. **Select any template and submit**

3. **Watch for bot activity (within 30 seconds):**
   - ✅ Welcome Bot should post a greeting comment
   - ✅ Auto-assign Bot should assign the issue
   - ✅ Copilot Bot should add labels

4. **Check the Actions tab:**
   ```
   https://github.com/Refactron-ai/Refactron_lib/actions
   ```
   - ✅ All workflows should complete successfully
   - ✅ No 403 errors

---

## 🔍 **Troubleshooting**

### **Issue: Workflows still fail with 403 errors**

**Possible causes:**
1. **Wrong secret name** - Must be exactly `BOT_TOKEN` (case-sensitive)
2. **Insufficient token scopes** - Make sure `repo` and `workflow` are selected
3. **Token expired** - Check expiration date and create a new one if needed
4. **Token not from org member** - Token must be from someone with repo access

**How to verify:**
- Go to: https://github.com/Refactron-ai/Refactron_lib/settings/secrets/actions
- Confirm `BOT_TOKEN` exists
- If you need to update it, click the trash icon and create a new secret

---

### **Issue: Token expired**

**Solution:**
1. Generate a new token following Step 1
2. Update the repository secret:
   - Go to secrets page
   - Click the trash icon next to `BOT_TOKEN`
   - Create a new secret with the same name and new token

---

### **Issue: Bots not triggering at all**

**Possible causes:**
1. **Workflows disabled** - Check Settings > Actions > General
2. **Branch protection** - Ensure workflows can run on main branch
3. **Action permissions** - Even with PAT, some org settings might block Actions

**How to fix:**
1. Go to: https://github.com/Refactron-ai/Refactron_lib/settings/actions
2. Under "Actions permissions", ensure:
   - ✅ "Allow all actions and reusable workflows" is selected
3. Scroll to "Workflow permissions" and verify settings

---

## 📊 **What's Been Updated**

All bot workflows now use the `BOT_TOKEN` secret:

| Workflow | File | Updated Actions |
|----------|------|-----------------|
| **Welcome Bot** | `welcome.yml` | 3 actions (issue, PR, member) |
| **Auto-assign** | `auto-assign.yml` | 2 actions (issue, PR) |
| **Copilot Bot** | `copilot-bot.yml` | 3 actions (label, PR label, commands) |
| **Auto-merge** | `auto-merge.yml` | 2 actions (merge, dependabot) |
| **Stale Bot** | `stale.yml` | 1 action (stale management) |

**Total:** 11 workflow actions updated to use PAT authentication

---

## 🔐 **Security Best Practices**

### **Token Security:**
- ✅ Never commit tokens to git
- ✅ Use repository secrets (not organization secrets for this use case)
- ✅ Regularly rotate tokens (every 6-12 months)
- ✅ Use minimal required scopes
- ✅ Monitor token usage in Settings > Developer settings > Personal access tokens

### **Token Permissions:**
The `repo` scope gives full repository access. This is necessary for:
- Creating comments on issues/PRs
- Adding/removing labels
- Assigning issues/PRs
- Closing/reopening issues
- Merging PRs

If you're concerned about security, you can:
1. Create a bot user account (separate GitHub account)
2. Add it as a collaborator to the repository
3. Generate the PAT from the bot account
4. This isolates bot actions from your personal account

---

## ✅ **Verification Checklist**

Before closing this guide, verify:

- [ ] Personal Access Token created with `repo` and `workflow` scopes
- [ ] Token added to repository secrets as `BOT_TOKEN`
- [ ] Test issue created to verify bot activity
- [ ] Welcome Bot posted a comment
- [ ] Auto-assign Bot assigned the issue
- [ ] Copilot Bot added labels
- [ ] All workflow runs show green checkmarks in Actions tab
- [ ] No 403 errors in workflow logs

---

## 🎯 **Alternative: Fix Organization Settings**

If you're an **organization owner**, you can fix this at the organization level instead:

1. **Go to Organization Settings:**
   ```
   https://github.com/organizations/Refactron-ai/settings/actions
   ```

2. **Navigate to:** Actions > General

3. **Scroll to "Workflow permissions"**

4. **Change to:**
   - ✅ "Read and write permissions"

5. **Enable:**
   - ✅ "Allow GitHub Actions to create and approve pull requests"

6. **Click "Save"**

**This would eliminate the need for the PAT**, but requires organization-level access and affects all repositories in the organization.

---

## 📞 **Need Help?**

If you're still experiencing issues:

1. **Check workflow logs:**
   - Go to Actions tab
   - Click on a failed workflow
   - Expand the failing step to see error details

2. **Verify secret:**
   - Ensure `BOT_TOKEN` is visible in repository secrets
   - Try regenerating the token if issues persist

3. **Contact support:**
   - Open an issue in the repository
   - Include workflow run URL and error message

---

## 📝 **Summary**

✅ **What was done:**
- All bot workflows updated to use `secrets.BOT_TOKEN`
- Workflows maintain full functionality with PAT authentication
- No changes to bot logic or permissions

✅ **What you need to do:**
1. Create a Personal Access Token with `repo` + `workflow` scopes
2. Add it as a repository secret named `BOT_TOKEN`
3. Test by creating a new issue

✅ **Expected outcome:**
- All 6 bots fully functional
- No more 403 permission errors
- Automated issue/PR management working perfectly

---

**Created:** $(date)  
**Status:** Ready for deployment  
**Action Required:** Add `BOT_TOKEN` secret to repository


