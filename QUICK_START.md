# ⚡ Quick Start Guide

Get Scanovich.ai running in 5 minutes!

## 🎯 **What You'll Need**
- **Python 3.8+** installed
- **Audio files** to analyze (WAV, MP3, M4A)
- **10GB+ free space** for models

## 🚀 **5-Minute Setup**

### **1. Clone & Install**
```bash
git clone https://github.com/FUYOH666/Scanovich.ai-audio-call.git
cd Scanovich.ai-audio-call

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### **2. Add Your Audio Files**
```bash
# Put your audio files here:
cp your-call.wav input/
```

### **3. Run Analysis**
```bash
# For single file analysis:
python enhanced_pipeline_v3.py

# For batch processing:
python batch_process.py
```

### **4. View Results**
```bash
# Open the generated report:
open output/reports/your-call_enhanced_report.html
```

## 📊 **What You Get**
- **📄 Detailed HTML report** with call analysis
- **📈 Quality scoring** (0-20 points)
- **🗣️ Speaker identification** 
- **📝 Full transcription** with timestamps
- **💡 Improvement recommendations**

## 🔧 **Common Issues**

### **"No module named 'whisperx'"**
```bash
pip install --upgrade whisperx torch torchaudio
```

### **"CUDA not available"**
```bash
# For Apple Silicon (M1/M2):
pip install torch torchvision torchaudio

# For NVIDIA GPUs:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### **"Permission denied"**
```bash
chmod +x *.py
```

## 🤝 **Need Help?**
- **📧 Email**: [iamfuyoh@gmail.com](mailto:iamfuyoh@gmail.com)
- **🐛 Bug reports**: [Create issue](https://github.com/FUYOH666/Scanovich.ai-audio-call/issues/new/choose)
- **💡 Feature requests**: [Create issue](https://github.com/FUYOH666/Scanovich.ai-audio-call/issues/new/choose)

## 🎯 **Next Steps**
- Read the full [README](README.md) for business information
- Check out [CONTRIBUTING](CONTRIBUTING.md) to get involved
- Explore [partnership opportunities](README.md#-looking-for-partners--mentors)

---

**Ready to analyze your calls? Let's go!** 🚀
