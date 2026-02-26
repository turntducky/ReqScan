# 📦 ReqScan - Dynamic `requirements.txt` Builder

> *"I got tired of manually tracking every import across every project. So I automated the suffering away."*

---

## 😤 The Problem

You know the drill. You've been smacking away on your keyboard for weeks. It's beautiful. It works. You're proud. Then someone says:

> *"Hey, can you send me the requirements?"*

And suddenly you're doing **archaeology** on your own code. Scrolling through 30 files. Squinting at imports. Trying to remember if you actually used `requests` or just thought about it. Manually checking versions. Forgetting one. Breaking their environment. Apologizing.

**No more.** ReqScan scans your entire project, figures out what you actually imported, cross-references it against what's installed, and spits out a clean `requirements.txt` all in seconds.

---

## ✨ Features

- 🔍 **Recursive project scanning** - walks your entire directory tree, skipping junk like `venv`, `node_modules`, `__pycache__`, and other things we don't talk about
- 🧠 **Smart import classification** - separates stdlib modules, local modules, and actual third-party dependencies (no more `os==3.11` nonsense)
- ⚡ **Parallel parsing** - uses `ProcessPoolExecutor` to parse files fast
- 🔄 **Merge mode** - keeps your manually-added entries and updates detected versions instead of nuking everything
- 📍 **Flexible output** - save the file inside your project or wherever you're running the script
- 🪟 **Windows compatible** - ANSI color support for those of us living in `cmd.exe` purgatory

---

---

## ⚡ Quick Install (pip)

Want the no-fuss version? Install it globally and use it anywhere:

```bash
pip install reqscan
```

Then just `cd` into any project and run:

```bash
reqscan
```

That's it. It scans the current directory and generates your `requirements.txt` on the spot — no prompts, no setup.

---


## 🚀 Full Version Usage

For the interactive experience with more options, clone this repo and run it directly:

```bash
python main.py
```

Then follow the prompts:

1. **Choose your project path** - current directory or a custom one
2. **Choose where to save** `requirements.txt` - inside the project or here
3. Watch it go 🎉

---

## 📋 Example Output

```
requirements.txt
────────────────
fastapi==0.111.0
httpx==0.27.0
pydantic==2.7.1
rich==13.7.1
uvicorn==0.29.0
```

Clean. Sorted. Versioned. Done.

---

## 🛠 Requirements

- Python 3.10+ (uses `sys.stdlib_module_names`, introduced in 3.10)
- No third-party dependencies, ReqScan eats its own food and requires nothing outside the stdlib

---

## ⚠️ Caveats & Known Quirks

- **Dynamic imports** (`importlib.import_module("something")`, `__import__`) won't be detected, ReqScan uses static AST analysis
- **Version detection** only works for packages installed in your current Python environment, run it from inside your virtualenv for best results
- If a package is imported under a different name than its PyPI name (e.g., `import cv2` → `opencv-python`), ReqScan uses `top_level.txt` metadata to resolve it, but some packages don't ship that file

---

## 🤝 Contributing

Found a bug? Have a wild idea? PRs welcome. This started as a personal itch-scratcher, so there's plenty of room to grow.

---

## 📜 License

Do whatever you want with it. Just don't manually maintain a `requirements.txt` ever again. That's the only rule.
