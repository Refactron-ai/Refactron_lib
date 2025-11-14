# 🤖 Auto-assign Bot - Command-based Assignment System

## 📋 **How It Works**

The Auto-assign Bot allows contributors to **self-assign issues** using simple comment commands.

---

## 🎯 **Available Commands**

### **Assignment Commands**
| Command | Description | Example |
|---------|-------------|---------|
| `/assign` | Assign this issue to yourself | Comment: `/assign` |
| `/unassign` | Remove your assignment from this issue | Comment: `/unassign` |

### **Help Commands**
| Command | Description | Example |
|---------|-------------|---------|
| `/help` | Show available commands | Comment: `/help` |
| `/commands` | Show available commands | Comment: `/commands` |

---

## 🚀 **How to Use**

### **Step 1: Find an Issue**
- Browse issues: https://github.com/Refactron-ai/Refactron_lib/issues
- Look for issues labeled `good-first-issue` or `help-wanted`

### **Step 2: Claim the Issue**
- Comment on the issue: `/assign`
- The bot will assign the issue to you
- You'll get a confirmation message

### **Step 3: Work on the Issue**
- Fork the repository
- Create a branch for your changes
- Make your changes
- Submit a pull request

### **Step 4: Reference the Issue**
- In your PR description, mention: `Fixes #123` or `Closes #123`
- This will automatically link your PR to the issue

---

## 📝 **Example Workflow**

```
👤 User: "I'd like to work on this issue!"
🤖 Bot: "Comment /assign to claim this issue"

👤 User: "/assign"
🤖 Bot: "✅ Successfully Assigned! This issue has been assigned to @username"

👤 User: [works on the issue, creates PR]
👤 User: "/unassign" (if they can't continue)
🤖 Bot: "✅ Assignment Removed. The issue is now available for others!"
```

---

## ⚠️ **Important Rules**

### **One Person Per Issue**
- ✅ Only **one person** can be assigned to an issue at a time
- ❌ If someone else is already assigned, you'll get an error message
- ✅ You can still comment and collaborate without being assigned

### **Self-Assignment Only**
- ✅ You can only assign **yourself** to issues
- ❌ You cannot assign other people
- ✅ This prevents spam and ensures genuine interest

### **Assignment Removal**
- ✅ You can unassign yourself anytime with `/unassign`
- ✅ This makes the issue available for others
- ✅ Use this if you can no longer work on the issue

---

## 🎯 **Bot Responses**

### **Successful Assignment**
```
✅ Successfully Assigned!

This issue has been assigned to @username.

Thank you for volunteering to work on this issue! 🚀

Next steps:
- Fork the repository
- Create a branch for your changes
- Make your changes
- Submit a pull request
- Reference this issue in your PR

Good luck! 💪
```

### **Already Assigned**
```
❌ Assignment Failed

This issue is already assigned to: @otheruser

Only one person can be assigned to an issue at a time.
If you'd like to collaborate, please comment on the issue instead! 💬
```

### **Unassignment**
```
✅ Assignment Removed

@username has unassigned themselves from this issue.

The issue is now available for others to claim! 🎯
```

---

## 🔧 **Technical Details**

- **Trigger:** Comments on issues
- **Commands:** Case-insensitive
- **Permissions:** Uses default GitHub Actions permissions
- **Response Time:** Usually within 30 seconds
- **Logs:** Available in Actions tab

---

## 🆘 **Troubleshooting**

### **Bot Not Responding**
1. Check if the comment contains exactly `/assign` (no extra spaces)
2. Wait up to 30 seconds for the bot to respond
3. Check the Actions tab for any errors

### **Assignment Failed**
1. Make sure the issue isn't already assigned to someone else
2. Try commenting `/help` to see available commands
3. Check if you have write access to the repository

### **Need Help**
- Comment `/help` on any issue to see available commands
- Check the Actions tab: https://github.com/Refactron-ai/Refactron_lib/actions
- Open a new issue if you encounter problems

---

## 📊 **Benefits**

✅ **Self-service** - Contributors can claim issues themselves
✅ **Fair** - First come, first served
✅ **Transparent** - Everyone can see who's working on what
✅ **Simple** - Just comment `/assign`
✅ **Flexible** - Can unassign if needed
✅ **No spam** - Only one person per issue

---

## 🎉 **Get Started**

1. **Find an issue** you want to work on
2. **Comment `/assign`** to claim it
3. **Start coding!** 🚀

**Happy contributing!** 🎊
