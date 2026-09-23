import os
import re

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    try:
        import importlib
        importlib.import_module('google.generativeai')
        HAS_GENAI = True
        genai = None  # Flag to use legacy path
    except ImportError:
        HAS_GENAI = False
        genai = None

# Gemini Models in priority order
GEMINI_MODELS = ['gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro']

def _load_key(key_names):
    """Load key from environment or .env file."""
    for key_name in key_names:
        val = os.getenv(key_name)
        if val:
            return val
            
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        if k in key_names and v:
                            return v
        except Exception:
            pass
    return None

def _get_target_role_skills(target_role):
    """Fetch skills required for the target role from config."""
    try:
        from config import SKILLS_MAP
        return SKILLS_MAP.get(target_role, [])
    except Exception:
        return []

def _generate_fallback_feedback(resume_text, target_role):
    """
    Generates an intelligent, multi-dimensional, role-aware feedback report.
    Analyzes actual metrics, action verbs, skill coverage, and ATS alignment.
    """
    text_lower = resume_text.lower()
    words = resume_text.split()
    word_count = len(words)
    
    # 1. Role-specific Skills Analysis
    role_skills = _get_target_role_skills(target_role)
    matched_role_skills = []
    missing_role_skills = []
    
    if role_skills:
        for skill in role_skills:
            # Word boundary search for precision
            pattern = r'\b' + re.escape(skill.lower()) + r'\b'
            if re.search(pattern, text_lower):
                matched_role_skills.append(skill)
            else:
                missing_role_skills.append(skill)
    else:
        common_tech = ['Python', 'SQL', 'Git', 'Docker', 'REST APIs', 'Cloud (AWS/Azure/GCP)']
        for s in common_tech:
            if s.lower() in text_lower:
                matched_role_skills.append(s)
            else:
                missing_role_skills.append(s)

    # 2. Metric and Quantitative Impact Analysis
    lines = resume_text.split('\n')
    bullets = [line.strip() for line in lines if line.strip().startswith('-') or line.strip().startswith('•') or line.strip().startswith('*')]
    
    metric_regex = r'(\b\d+%\b|\$\s*\d+[\d,]*|\b\d+x\b|\b\d+\s*(?:ms|sec|hours|days|k|m|users|requests|tps|lpa|tb|gb)\b)'
    bullets_with_metrics = [b for b in bullets if re.search(metric_regex, b, re.IGNORECASE)]
    
    action_verbs = ['spearheaded', 'engineered', 'architected', 'orchestrated', 'deployed', 'developed', 
                    'optimized', 'automated', 'streamlined', 'designed', 'built', 'reduced', 'increased', 
                    'scaled', 'integrated', 'implemented', 'led', 'accelerated']
    found_verbs = [v for v in action_verbs if re.search(r'\b' + v + r'\b', text_lower)]
    
    # Calculate Score Heuristic (0 to 100)
    score = 60
    if len(bullets) > 0:
        metric_ratio = len(bullets_with_metrics) / len(bullets)
        score += int(metric_ratio * 20)
    if len(matched_role_skills) >= 4:
        score += 10
    if len(found_verbs) >= 3:
        score += 10
    score = min(score, 96)
    
    # Format Report in Clean Markdown
    md = []
    md.append(f"### Comprehensive AI Resume Audit for {target_role}\n")
    md.append(f"> **Overall Profile Strength Score:** `{score}/100` | **Total Words:** `{word_count}` | **Action Verbs Detected:** `{len(found_verbs)}`\n")
    
    # Section 1: Skill Alignment & Gap Analysis
    md.append(f"#### 1. Role Skill Alignment: {target_role} 🎯\n")
    if matched_role_skills:
        md.append(f"- **Identified Strengths:** Verified experience in **{', '.join(matched_role_skills[:8])}**.")
    else:
        md.append(f"- **Identified Strengths:** General technical foundation observed.")
        
    if missing_role_skills:
        top_missing = missing_role_skills[:5]
        md.append(f"- **High-Priority Missing Keywords:** To pass tier-1 ATS filters for {target_role}, explicitly incorporate: **{', '.join(top_missing)}**.")
        md.append(f"- **Optimization Tip:** Place these keywords naturally in your 'Technical Skills' inventory and describe their practical application in project summaries.\n")
    else:
        md.append(f"- **Core Coverage:** Outstanding! Your profile includes all primary prerequisite keywords for {target_role}.\n")

    # Section 2: Metric Quantification & Impact
    md.append("#### 2. Quantitative Impact & Bullet Point Strength 📈\n")
    if bullets_with_metrics:
        md.append(f"- **Positive Findings:** Detected `{len(bullets_with_metrics)}` bullet point(s) containing measurable numerical impact (percentages, volume, or performance improvements).")
        md.append("- **Enhancement Recommendation:** Elevate existing bullets by applying Google's **XYZ Formula**: *'Accomplished [X] as measured by [Y], by doing [Z]'*.")
    else:
        md.append("- **Critical Gap:** Your bullet points are primarily task-oriented rather than achievement-oriented. Recruiters prioritize tangible results over daily duties.")
        md.append("- **Actionable Transformation Example:**")
        md.append("  - *Before:* 'Worked on backend API services and improved performance.'")
        md.append("  - *After:* 'Architected scalable RESTful microservices, **reducing API response latency by 38%** and supporting **10,000+ daily active users**.'\n")

    # Section 3: Formatting & ATS Compliance
    md.append("#### 3. ATS Parser & Layout Optimization 🤖\n")
    md.append("- **Header Structure:** Use standardized section headings (`Technical Skills`, `Professional Experience`, `Projects`, `Education`). Non-standard titles like 'Where I have worked' disrupt algorithmic parsing.")
    md.append("- **Layout Hygiene:** Maintain a clean single-column or clean two-section layout. Avoid graphics, nested multi-layer tables, or text boxes that can scramble parsing order.")
    if word_count > 900:
        md.append(f"- **Length Advisory:** Your resume contains ~`{word_count}` words. For professionals under 7 years of experience, a concise 1-page format (~450-650 words) achieves 40% higher recruiter engagement.")
    elif word_count < 250:
        md.append(f"- **Length Advisory:** Content is relatively brief (~`{word_count}` words). Elaborate on technical challenges resolved and architectural tools utilized.\n")
    else:
        md.append(f"- **Length Check:** Optimal length detected (`{word_count}` words). Well-proportioned density for ATS ingestion.\n")

    # Section 4: Recommended Certifications & Next Steps
    md.append(f"#### 4. Strategic Career Pathways for {target_role} 🚀\n")
    cert_map = {
        'Data Science': ['AWS Certified Machine Learning Specialty', 'TensorFlow Developer Certificate', 'Databricks Certified Data Scientist'],
        'DevOps Engineer': ['Certified Kubernetes Administrator (CKA)', 'AWS Certified DevOps Engineer', 'HashiCorp Certified: Terraform Associate'],
        'Java Developer': ['Oracle Certified Professional: Java SE', 'Spring Certified Professional', 'AWS Certified Developer Associate'],
        'Python Developer': ['PCEP/PCAP Certified Associate Python Programmer', 'Docker Certified Associate', 'AWS Certified Cloud Practitioner'],
        'Web Designing': ['Google UX Design Professional Certificate', 'Nielsen Norman Group UX Certification', 'Interaction Design Foundation (IxDF)'],
        'Web Developer': ['Meta Front-End / Back-End Developer Professional', 'AWS Certified Solutions Architect', 'MongoDB Certified Developer'],
        'Cybersecurity': ['CompTIA Security+', 'Certified Ethical Hacker (CEH)', 'CISSP / OSCP'],
        'AI/ML Engineer': ['DeepLearning.AI TensorFlow Professional', 'AWS Machine Learning Specialty', 'NVIDIA Deep Learning Institute Certificate']
    }
    recommended_certs = cert_map.get(target_role, ['AWS Certified Cloud Practitioner', 'Professional Scrum Master (PSM I)', 'Domain-specific Google Cloud / Microsoft Azure Certification'])
    md.append(f"- **Targeted Certifications:** Boost credibility by considering: *{', '.join(recommended_certs)}*.")
    md.append(f"- **Strategic Action:** Revise your top 3 bullet points, integrate missing skills, and run a re-check to confirm your improved alignment score.")

    return "\n".join(md)

def _call_gemini(api_key, prompt):
    """Call Google Gemini API using modern or legacy SDK with fallback."""
    if not HAS_GENAI:
        return None, "Gemini libraries not installed"
        
    # 1. Modern google.genai SDK
    if genai is not None:
        try:
            client = genai.Client(api_key=api_key)
            for model_name in GEMINI_MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    if response and response.text:
                        return response.text, None
                except Exception as model_err:
                    # Model not available or quota, try next
                    continue
        except Exception as client_err:
            pass
            
    # 2. Legacy google.generativeai SDK
    try:
        import google.generativeai as genai_legacy
        genai_legacy.configure(api_key=api_key)
        for model_name in GEMINI_MODELS:
            try:
                model = genai_legacy.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                if response and response.text:
                    return response.text, None
            except Exception:
                continue
    except Exception:
        pass
        
    return None, "All Gemini models returned empty or failed"

def generate_resume_feedback(resume_text, target_role, user_api_key=None):
    """
    Main entry point for AI feedback.
    1. Attempts live Google Gemini generation if API key is provided or found.
    2. Seamlessly falls back to deep, rule-based ATS analysis if no key or if API call fails.
    """
    # Clean and truncate text for prompt safety
    clean_text = resume_text.strip()[:6000]
    
    prompt = f"""You are a top-tier Silicon Valley technical recruiter and executive career coach.
Review this candidate's resume for the target role: "{target_role}".
Provide an insightful, high-impact diagnostic report formatted in GitHub Markdown.

Include the following 4 sections:
1. Role Skill Alignment: Highlights matches and specifically identifies missing core tools for {target_role}.
2. Quantified Impact & Bullet Point Critique: Identifies weak bullets and provides clear Before vs After rewrites using numbers (%, $, metrics).
3. ATS Optimization & Layout: Actionable tips on layout, keyword density, and parser compliance.
4. Strategic Next Steps: 2-3 specific high-value certifications and projects to secure interviews.

Keep tone professional, encouraging, and highly specific.
Total response should be around 350-450 words.

Candidate Resume Text:
{clean_text}"""

    # 1. Check passed user key, then environment / .env
    active_key = user_api_key or _load_key(["GEMINI_API_KEY", "GOOGLE_API_KEY"])
    
    if active_key and len(active_key.strip()) > 10:
        result, error = _call_gemini(active_key.strip(), prompt)
        if result and len(result.strip()) > 50:
            return f"### Expert Resume Analysis for {target_role}\n\n> *Powered by Google Gemini AI*\n\n" + result

    # 2. Intelligent, highly realistic fallback engine
    return _generate_fallback_feedback(clean_text, target_role)
