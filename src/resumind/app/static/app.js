document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('file-input');
    const uploadZone = document.getElementById('upload-zone');
    const fileNameDisplay = document.getElementById('file-name-display');
    const analyzeBtn = document.getElementById('analyze-btn');
    const errorBanner = document.getElementById('error-message');
    
    const uploadSection = document.getElementById('upload-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    
    const viewJsonBtn = document.getElementById('view-json-btn');
    const resetBtn = document.getElementById('reset-btn');
    const jsonModal = document.getElementById('json-modal');
    const closeModalBtn = document.getElementById('close-modal-btn');
    const copyJsonBtn = document.getElementById('copy-json-btn');
    const jsonOutput = document.getElementById('json-output');

    let selectedFile = null;
    let currentResumeData = null;

    // --- File Selection & Drag/Drop ---
    const handleFileSelect = (file) => {
        if (!file) return;
        selectedFile = file;
        fileNameDisplay.textContent = file.name;
        analyzeBtn.disabled = false;
        errorBanner.classList.add('hidden');
    };

    fileInput.addEventListener('change', (e) => {
        handleFileSelect(e.target.files[0]);
    });

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('dragover');
    });

    uploadZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0]);
            fileInput.files = e.dataTransfer.files; // sync
        }
    });

    // --- Utility: Safe Text HTML ---
    const escapeHTML = (str) => {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    };

    const renderList = (items) => {
        if (!items || !items.length) return '';
        return `<ul>${items.map(item => `<li>${escapeHTML(item)}</li>`).join('')}</ul>`;
    };

    // --- Parsing Flow ---
    analyzeBtn.addEventListener('click', async () => {
        if (!selectedFile) return;

        // UI State -> Loading
        uploadSection.classList.add('hidden');
        errorBanner.classList.add('hidden');
        loadingSection.classList.remove('hidden');

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const response = await fetch('/api/v1/resumes/parse', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error ? data.error.message : 'Unknown error occurred.');
            }

            renderResults(data);
            currentResumeData = data;

            // UI State -> Results
            loadingSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');

        } catch (error) {
            // UI State -> Error
            loadingSection.classList.add('hidden');
            uploadSection.classList.remove('hidden');
            errorBanner.textContent = error.message || 'Unable to connect to the Resumind server.';
            errorBanner.classList.remove('hidden');
        }
    });

    // --- Rendering Results ---
    const renderResults = (data) => {
        const resume = data.resume;
        if (!resume) return;

        // 1. Warnings
        const warningsContainer = document.getElementById('warnings-container');
        if (data.warnings && data.warnings.length > 0) {
            warningsContainer.innerHTML = `<strong>Warnings:</strong><ul>${data.warnings.map(w => `<li>${escapeHTML(w)}</li>`).join('')}</ul>`;
            warningsContainer.classList.remove('hidden');
        } else {
            warningsContainer.classList.add('hidden');
        }

        // 2. Candidate
        const candidateCard = document.getElementById('candidate-card');
        if (resume.candidate && resume.candidate.name) {
            let linksHTML = [];
            const c = resume.contact;
            if (c.email) linksHTML.push(`<span>✉ ${escapeHTML(c.email)}</span>`);
            if (c.phone) linksHTML.push(`<span>☎ ${escapeHTML(c.phone)}</span>`);
            if (resume.candidate.location) linksHTML.push(`<span>📍 ${escapeHTML(resume.candidate.location)}</span>`);
            if (c.github && c.github.length) linksHTML.push(`<a href="${escapeHTML(c.github[0])}" target="_blank">GitHub</a>`);
            if (c.linkedin && c.linkedin.length) linksHTML.push(`<a href="${escapeHTML(c.linkedin[0])}" target="_blank">LinkedIn</a>`);
            if (c.portfolio) linksHTML.push(`<a href="${escapeHTML(c.portfolio)}" target="_blank">Portfolio</a>`);

            candidateCard.innerHTML = `
                <h2>${escapeHTML(resume.candidate.name)}</h2>
                <div class="contact-links">${linksHTML.join('')}</div>
            `;
            candidateCard.classList.remove('hidden');
        } else {
            candidateCard.classList.add('hidden');
        }

        // 3. Summary
        const summaryCard = document.getElementById('summary-card');
        if (resume.summary) {
            summaryCard.innerHTML = `<h3>Summary</h3><p>${escapeHTML(resume.summary)}</p>`;
            summaryCard.classList.remove('hidden');
        } else {
            summaryCard.classList.add('hidden');
        }

        // 4. Skills
        const skillsCard = document.getElementById('skills-card');
        const skillsList = document.getElementById('skills-list');
        if (resume.skills && resume.skills.length > 0) {
            const categorized = {};
            resume.skills.forEach(s => {
                const cat = s.category || 'Other';
                if (!categorized[cat]) categorized[cat] = [];
                categorized[cat].push(s.canonical_name);
            });

            skillsList.innerHTML = Object.keys(categorized).map(cat => `
                <div class="skill-category">
                    <h4>${escapeHTML(cat)}</h4>
                    <div class="skill-tags">
                        ${categorized[cat].map(s => `<span class="skill-tag">${escapeHTML(s)}</span>`).join('')}
                    </div>
                </div>
            `).join('');
            skillsCard.classList.remove('hidden');
        } else {
            skillsCard.classList.add('hidden');
        }

        // 5. Experience
        const expCard = document.getElementById('experience-card');
        const expList = document.getElementById('experience-list');
        if (resume.experience && resume.experience.length > 0) {
            expList.innerHTML = resume.experience.map(exp => `
                <div class="timeline-item">
                    <div class="timeline-header">
                        <span class="timeline-title">${escapeHTML(exp.role || 'Unknown Role')}</span>
                        <span class="timeline-date">${escapeHTML(exp.start_date || '')} - ${exp.is_current ? 'Present' : escapeHTML(exp.end_date || '')}</span>
                    </div>
                    <div class="timeline-subtitle">${escapeHTML(exp.organization || '')} ${exp.location ? ` | ${escapeHTML(exp.location)}` : ''}</div>
                    <div class="timeline-desc">
                        ${renderList(exp.description)}
                        ${exp.skills && exp.skills.length ? `<div style="margin-top: 8px"><small><strong>Technologies:</strong> ${escapeHTML(exp.skills.join(', '))}</small></div>` : ''}
                    </div>
                </div>
            `).join('');
            expCard.classList.remove('hidden');
        } else {
            expCard.classList.add('hidden');
        }

        // 6. Education
        const eduCard = document.getElementById('education-card');
        const eduList = document.getElementById('education-list');
        if (resume.education && resume.education.length > 0) {
            eduList.innerHTML = resume.education.map(edu => `
                <div class="timeline-item">
                    <div class="timeline-header">
                        <span class="timeline-title">${escapeHTML(edu.institution || 'Unknown Institution')}</span>
                        <span class="timeline-date">${escapeHTML(edu.start_date || '')} - ${escapeHTML(edu.end_date || '')}</span>
                    </div>
                    <div class="timeline-subtitle">${escapeHTML(edu.degree || '')}</div>
                    ${edu.grade ? `<div class="timeline-desc"><small>Grade: ${escapeHTML(edu.grade)}</small></div>` : ''}
                </div>
            `).join('');
            eduCard.classList.remove('hidden');
        } else {
            eduCard.classList.add('hidden');
        }

        // 7. Projects
        const projCard = document.getElementById('projects-card');
        const projList = document.getElementById('projects-list');
        if (resume.projects && resume.projects.length > 0) {
            projList.innerHTML = resume.projects.map(proj => `
                <div class="timeline-item">
                    <div class="timeline-header">
                        <span class="timeline-title">${escapeHTML(proj.name || 'Project')}</span>
                        <span class="timeline-date">${escapeHTML(proj.start_date || '')} - ${escapeHTML(proj.end_date || '')}</span>
                    </div>
                    <div class="timeline-desc">
                        <p>${escapeHTML(proj.description || '')}</p>
                        ${proj.technologies && proj.technologies.length ? `<div style="margin-top: 8px"><small><strong>Technologies:</strong> ${escapeHTML(proj.technologies.join(', '))}</small></div>` : ''}
                    </div>
                </div>
            `).join('');
            projCard.classList.remove('hidden');
        } else {
            projCard.classList.add('hidden');
        }
    };

    // --- UI Controls ---
    resetBtn.addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        uploadSection.classList.remove('hidden');
        fileInput.value = '';
        selectedFile = null;
        fileNameDisplay.textContent = '';
        analyzeBtn.disabled = true;
        currentResumeData = null;
    });

    viewJsonBtn.addEventListener('click', () => {
        if (currentResumeData) {
            jsonOutput.textContent = JSON.stringify(currentResumeData, null, 2);
            jsonModal.classList.remove('hidden');
        }
    });

    closeModalBtn.addEventListener('click', () => {
        jsonModal.classList.add('hidden');
    });

    copyJsonBtn.addEventListener('click', () => {
        if (currentResumeData) {
            navigator.clipboard.writeText(JSON.stringify(currentResumeData, null, 2))
                .then(() => {
                    const originalText = copyJsonBtn.textContent;
                    copyJsonBtn.textContent = 'Copied!';
                    setTimeout(() => { copyJsonBtn.textContent = originalText; }, 2000);
                })
                .catch(err => {
                    alert('Failed to copy JSON.');
                });
        }
    });
});
