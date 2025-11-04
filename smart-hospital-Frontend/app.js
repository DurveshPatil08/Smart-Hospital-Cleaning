document.addEventListener("DOMContentLoaded", () => {
    const mainContent = document.getElementById("main-content");
    const logoutButton = document.getElementById("logout-button");
    const messageBox = document.getElementById("message-box");

    const API_BASE_URL = "http://127.0.0.1:5000";

    const showMessage = (message, isError = false) => {
        const icon = isError ? '<i class="fas fa-exclamation-circle"></i>' : '<i class="fas fa-check-circle"></i>';
        messageBox.innerHTML = `${icon}<span>${message}</span>`;
        messageBox.className = `fixed top-5 right-5 p-4 rounded-lg shadow-2xl text-white flex items-center gap-3 text-lg glass-effect border ${
            isError ? 'border-red-500/50' : 'border-green-500/50'
        } fade-in`;
        messageBox.classList.remove("hidden");
        setTimeout(() => {
            messageBox.classList.add("hidden");
        }, 3000);
    };

    const getToken = () => localStorage.getItem("jwt_token");

    const getUserData = () => {
        const token = getToken();
        if (!token) return null;
        try {
            return JSON.parse(atob(token.split('.')[1]));
        } catch (e) {
            console.error("Failed to parse token:", e);
            logout(); // Corrupted token, force logout
            return null;
        }
    };

    const loadPage = async (page) => {
        try {
            const response = await fetch(`./pages/${page}.html`);
            if (!response.ok) throw new Error("Page not found");
            mainContent.innerHTML = await response.text();
            initializePageSpecificLogic(page);
        } catch (error) {
            mainContent.innerHTML = `<p class="text-red-400 text-center">Error loading page: ${error.message}</p>`;
        }
    };

    const router = () => {
        const userData = getUserData();
        if (userData) {
            logoutButton.classList.remove("hidden");
            const userRole = userData.role;
            if (userRole === "cleaner") loadPage("cleaner");
            else if (userRole === "manager") loadPage("manager");
            else if (userRole === "dean" || userRole === "bmc_commissioner") loadPage("admin");
            else logout();
        } else {
            logoutButton.classList.add("hidden");
            window.location.hash === "#register" ? loadPage("register") : loadPage("login");
        }
    };

    const initializePageSpecificLogic = (page) => {
        const pageLoaders = {
            login: setupLoginForm,
            register: setupRegisterForm,
            cleaner: setupCleanerDashboard,
            manager: setupManagerDashboard,
            admin: setupAdminDashboard,
        };
        if (pageLoaders[page]) pageLoaders[page]();
    };
    
    // --- FORM HANDLERS ---
    
    const setupLoginForm = () => {
        const form = document.getElementById("login-form");
        if (!form) return;
        
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            
            localStorage.removeItem("jwt_token");
            const data = Object.fromEntries(new FormData(form).entries());

            try {
                const response = await fetch(`${API_BASE_URL}/login`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });
                const result = await response.json();
                if (!result.success) throw new Error(result.message);
                localStorage.setItem("jwt_token", result.token);
                showMessage("Login successful!");
                router();
            } catch (error) {
                showMessage(error.message, true);
                submitButton.disabled = false;
            }
        });

        document.getElementById("register-link")?.addEventListener("click", (e) => {
            e.preventDefault();
            window.location.hash = "#register";
            router();
        });
    };
    
    const setupRegisterForm = () => {
        const form = document.getElementById("register-form");
        if (!form) return;

        const roleSelect = form.querySelector("#role");
        const hospitalDiv = form.querySelector("#hospital-select-div");
        const hospitalSelect = form.querySelector("#hospital");

        const toggleHospital = () => {
            if (roleSelect.value !== 'bmc_commissioner') {
                hospitalDiv.classList.remove('hidden');
                hospitalSelect.required = true;
            } else {
                hospitalDiv.classList.add('hidden');
                hospitalSelect.required = false;
            }
        };

        fetch(`${API_BASE_URL}/hospitals`).then(res => res.json()).then(result => {
            if (result.success) {
                hospitalSelect.innerHTML = result.data.map(h => `<option value="${h.id}">${h.name}</option>`).join('');
            }
        });

        roleSelect.addEventListener('change', toggleHospital);
        toggleHospital();

        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitButton = form.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            if (data.role !== 'bmc_commissioner') data.hospital_id = data.hospital;

            try {
                const response = await fetch(`${API_BASE_URL}/register`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(data),
                });
                const result = await response.json();
                if (!result.success) throw new Error(result.message);
                showMessage("Registration successful! Please log in.");
                window.location.hash = "#login";
                router();
            } catch (error) {
                showMessage(error.message, true);
                submitButton.disabled = false;
            }
        });

        document.getElementById("login-link")?.addEventListener("click", (e) => {
            e.preventDefault();
            window.location.hash = "#login";
            router();
        });
    };

    const setupCleanerDashboard = () => {
        // Add user welcome section
        const userData = getUserData();
        const welcomeElement = document.createElement('div');
        welcomeElement.className = 'mb-6 p-4 glass-effect rounded-lg border border-gray-700 fade-in';
        welcomeElement.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-semibold">
                    ${userData.full_name ? userData.full_name.charAt(0).toUpperCase() : 'C'}
                </div>
                <div>
                    <h3 class="text-white font-semibold">Welcome back, ${userData.full_name || 'Cleaner'}!</h3>
                    <p class="text-gray-400 text-sm">Ready to submit your work?</p>
                </div>
            </div>
        `;
        const firstCard = document.querySelector('.card-hover');
        if (firstCard) {
            firstCard.parentNode.insertBefore(welcomeElement, firstCard);
        }

        const uploadForm = document.getElementById("upload-form");
        if (uploadForm) {
            const submitButton = uploadForm.querySelector("#upload-submit-button");
            const spinner = uploadForm.querySelector("#upload-spinner");
            const buttonText = uploadForm.querySelector("#upload-button-text");
            
            // Add file upload drag and drop functionality
            const fileUploadArea = uploadForm.querySelector('.file-upload-area');
            const fileInput = uploadForm.querySelector('#photo');
            
            if (fileUploadArea && fileInput) {
                fileUploadArea.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    fileUploadArea.classList.add('dragover');
                });
                
                fileUploadArea.addEventListener('dragleave', () => {
                    fileUploadArea.classList.remove('dragover');
                });
                
                fileUploadArea.addEventListener('drop', (e) => {
                    e.preventDefault();
                    fileUploadArea.classList.remove('dragover');
                    if (e.dataTransfer.files.length) {
                        fileInput.files = e.dataTransfer.files;
                    }
                });
                
                fileInput.addEventListener('change', () => {
                    if (fileInput.files.length) {
                        fileUploadArea.innerHTML = `
                            <i class="fas fa-check text-green-400 text-3xl mb-3"></i>
                            <p class="text-green-400 font-medium mb-2">File selected</p>
                            <p class="text-sm text-gray-400">${fileInput.files[0].name}</p>
                        `;
                    }
                });
            }
            
            uploadForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                submitButton.disabled = true;
                spinner.classList.remove('hidden');
                buttonText.textContent = 'Submitting...';
                
                const formData = new FormData();
                formData.append('room_id', uploadForm.querySelector('#room').value);
                formData.append('after_photo', uploadForm.querySelector('#photo').files[0]);
                formData.append('cleaner_id', getUserData().user_id);
                
                try {
                    const response = await fetch(`${API_BASE_URL}/verify_room`, { method: "POST", body: formData });
                    const result = await response.json();
                    if (!result.success) throw new Error(result.error || "Submission failed.");
                    showMessage("Work submitted for verification.");
                    uploadForm.reset();
                    // Reset file upload area
                    if (fileUploadArea) {
                        fileUploadArea.innerHTML = `
                            <i class="fas fa-camera text-3xl text-gray-400 mb-3"></i>
                            <p class="text-gray-300 mb-2">Click to upload or drag and drop</p>
                            <p class="text-sm text-gray-500">PNG, JPG, WEBP (Max. 10MB)</p>
                            <input type="file" id="photo" name="photo" required accept="image/*" class="w-full mt-3">
                        `;
                    }
                } catch (error) {
                    showMessage(error.message, true);
                } finally {
                    submitButton.disabled = false;
                    spinner.classList.add('hidden');
                    buttonText.textContent = 'Submit for Verification';
                }
            });
        }
        
        const taskListDiv = document.getElementById("task-list");
        if (taskListDiv) {
            fetch(`${API_BASE_URL}/tasks/${getUserData().user_id}`).then(res => res.json()).then(result => {
                if (!result.success || result.data.length === 0) {
                    taskListDiv.innerHTML = `
                        <div class="text-center py-8">
                            <i class="fas fa-clipboard-list text-3xl text-gray-500 mb-3"></i>
                            <p class="text-gray-400">No tasks assigned currently.</p>
                            <p class="text-sm text-gray-500 mt-1">Check back later for new assignments</p>
                        </div>
                    `;
                    return;
                }
                taskListDiv.innerHTML = result.data.map(task => `
                    <div class="p-4 glass-effect rounded-lg border border-gray-700 transition-all duration-300 hover:border-blue-500/50">
                        <div class="flex justify-between items-center">
                            <h4 class="font-bold text-lg text-white">${task.room_id}</h4>
                            <span class="status-badge ${task.status === 'Pending' ? 'pending' : 'completed'}">${task.status}</span>
                        </div>
                        <p class="text-sm text-gray-400 mt-1"><strong>Date:</strong> ${new Date(task.assignment_date).toLocaleDateString()}</p>
                        <p class="mt-2 text-gray-300 bg-gray-800/50 p-2 rounded-md">${task.notes || 'No notes provided.'}</p>
                    </div>
                `).join('');
            }).catch(error => {
                taskListDiv.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-exclamation-triangle text-2xl text-red-400 mb-3"></i>
                        <p class="text-red-400">Failed to load tasks</p>
                        <p class="text-sm text-gray-400 mt-1">Please try again later</p>
                    </div>
                `;
            });
        }
    };

    const setupManagerDashboard = () => {
        // Add manager welcome section
        const userData = getUserData();
        const welcomeElement = document.createElement('div');
        welcomeElement.className = 'mb-6 p-4 glass-effect rounded-lg border border-gray-700 fade-in';
        welcomeElement.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center text-white font-semibold">
                    ${userData.full_name ? userData.full_name.charAt(0).toUpperCase() : 'M'}
                </div>
                <div>
                    <h3 class="text-white font-semibold">Manager Dashboard</h3>
                    <p class="text-gray-400 text-sm">Welcome back, ${userData.full_name || 'Manager'}!</p>
                </div>
            </div>
        `;
        const firstCard = document.querySelector('.card-hover');
        if (firstCard) {
            firstCard.parentNode.insertBefore(welcomeElement, firstCard);
        }

        const cleanerSelect = document.getElementById("cleaner");
        
        if (cleanerSelect) {
            fetch(`${API_BASE_URL}/cleaners`, { headers: { 'Authorization': `Bearer ${getToken()}` }})
            .then(res => res.json()).then(result => {
                if (result.success && result.data.length > 0) {
                    cleanerSelect.innerHTML = '<option value="" disabled selected>Select a cleaner</option>' + 
                    result.data.map(c => `<option value="${c.id}">${c.full_name}</option>`).join('');
                } else {
                    cleanerSelect.innerHTML = `<option value="" disabled>${result.error || "No cleaners found"}</option>`;
                }
            });
        }

        const assignTaskForm = document.getElementById("assign-task-form");
        if (assignTaskForm) {
            // Set default date to today
            const dateInput = assignTaskForm.querySelector('#date');
            if (dateInput) {
                const today = new Date().toISOString().split('T')[0];
                dateInput.value = today;
                dateInput.min = today; // Prevent selecting past dates
            }

            assignTaskForm.addEventListener("submit", async (e) => {
                e.preventDefault();
                const submitButton = assignTaskForm.querySelector('button[type="submit"]');
                submitButton.disabled = true;

                const data = { ...Object.fromEntries(new FormData(assignTaskForm).entries()), assigned_by_id: userData.user_id };
                data.cleaner_id = data.cleaner;

                try {
                    const response = await fetch(`${API_BASE_URL}/assign_task`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    const result = await response.json();
                    if (!result.success) throw new Error(result.message || "Failed to assign task.");
                    showMessage("Task assigned successfully.");
                    assignTaskForm.reset();
                    // Reset date to today
                    if (dateInput) {
                        dateInput.value = today;
                    }
                    cleanerSelect.selectedIndex = 0;
                } catch (error) {
                    showMessage(error.message, true);
                } finally {
                    submitButton.disabled = false;
                }
            });
        }

        const approvalList = document.getElementById("approval-list");
        const loadApprovals = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/dashboard`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
                const result = await response.json();
                if (!result.success || result.data.length === 0) {
                    approvalList.innerHTML = `
                        <div class="text-center py-8">
                            <i class="fas fa-check-circle text-3xl text-green-400 mb-3"></i>
                            <p class="text-gray-400">All caught up!</p>
                            <p class="text-sm text-gray-500 mt-1">No items pending approval</p>
                        </div>
                    `;
                    return;
                }
                approvalList.innerHTML = result.data.map(item => {
                    const statusColor = item.cleanliness_status === 'Clean' ? 'status-clean' : 
                                      (item.cleanliness_status === 'Partially Clean' ? 'status-partial' : 'status-dirty');
                    return `
                    <div class="p-4 glass-effect rounded-lg border border-gray-700 transition-all duration-300 hover:border-yellow-500/50" id="record-${item.id}">
                        <h4 class="font-bold text-lg text-white">${item.room_id}</h4>
                        <p class="text-sm text-gray-400">Cleaner: ${item.cleaner_id.substring(0,8)}...</p>
                        <div class="flex items-center gap-2 my-3">
                            <span class="font-semibold text-gray-300">AI Status:</span>
                            <span class="status-dot ${statusColor}"></span>
                            <span class="text-gray-300">${item.cleanliness_status}</span>
                        </div>
                        <p class="text-gray-300 bg-gray-800/50 p-3 rounded-md italic border-l-4 border-blue-500">"${item.ai_remarks}"</p>
                        <div class="mt-4 flex gap-2">
                            <button class="approve-btn flex-1 btn-success text-white px-3 py-3 rounded-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50" data-id="${item.id}">
                                <i class="fas fa-check"></i>
                                <span>Approve</span>
                            </button>
                            <button class="rework-btn flex-1 btn-warning text-white px-3 py-3 rounded-lg font-semibold flex items-center justify-center gap-2 disabled:opacity-50" data-id="${item.id}">
                                <i class="fas fa-redo"></i>
                                <span>Rework</span>
                            </button>
                        </div>
                    </div>
                `}).join('');
            } catch (error) {
                approvalList.innerHTML = `
                    <div class="text-center py-8">
                        <i class="fas fa-exclamation-triangle text-2xl text-red-400 mb-3"></i>
                        <p class="text-red-400">Failed to load approvals</p>
                        <p class="text-sm text-gray-400 mt-1">Please try again later</p>
                    </div>
                `;
            }
        };
        
        if (approvalList) {
            approvalList.addEventListener("click", async (e) => {
                const button = e.target.closest("button");
                if (!button) return;

                const recordId = button.dataset.id;
                const newStatus = button.classList.contains("approve-btn") ? "Approved" : "Rework";
                
                const allButtons = button.parentElement.querySelectorAll('button');
                allButtons.forEach(btn => btn.disabled = true);
                
                try {
                    const response = await fetch(`${API_BASE_URL}/approve`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
                        body: JSON.stringify({ record_id: parseInt(recordId), new_status: newStatus })
                    });
                    const result = await response.json();
                    if (!result.success) throw new Error(result.message || result.error);
                    showMessage(`Record ${newStatus.toLowerCase()} successfully.`);
                    document.getElementById(`record-${recordId}`).remove();
                    
                    // Check if no approvals left
                    if (approvalList.children.length === 0) {
                        approvalList.innerHTML = `
                            <div class="text-center py-8">
                                <i class="fas fa-check-circle text-3xl text-green-400 mb-3"></i>
                                <p class="text-gray-400">All caught up!</p>
                                <p class="text-sm text-gray-500 mt-1">No items pending approval</p>
                            </div>
                        `;
                    }
                } catch(error) {
                    showMessage(error.message, true);
                    allButtons.forEach(btn => btn.disabled = false);
                }
            });
            loadApprovals();
        }
    };
    
    const setupAdminDashboard = () => {
        // Add admin welcome section
        const userData = getUserData();
        const welcomeElement = document.createElement('div');
        welcomeElement.className = 'mb-6 p-4 glass-effect rounded-lg border border-gray-700 fade-in';
        welcomeElement.innerHTML = `
            <div class="flex items-center gap-3">
                <div class="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center text-white font-semibold">
                    ${userData.full_name ? userData.full_name.charAt(0).toUpperCase() : 'A'}
                </div>
                <div>
                    <h3 class="text-white font-semibold">Administrative Dashboard</h3>
                    <p class="text-gray-400 text-sm">Welcome back, ${userData.full_name || 'Admin'}!</p>
                </div>
            </div>
        `;
        const mainContainer = document.querySelector('.max-w-4xl');
        if (mainContainer) {
            mainContainer.parentNode.insertBefore(welcomeElement, mainContainer);
        }

        const downloadBtn = document.getElementById("download-report-button");
        const roleDisplay = document.getElementById("admin-role-display");
        const userDataForRole = getUserData();

        if (roleDisplay && userDataForRole) {
            roleDisplay.textContent = userDataForRole.role === 'bmc_commissioner' ? 'a Commissioner' : 'the Dean';
        }
        
        if (downloadBtn) {
            downloadBtn.addEventListener("click", async () => {
                downloadBtn.disabled = true;
                const buttonText = downloadBtn.querySelector('span');
                const originalText = buttonText.textContent;
                buttonText.textContent = 'Generating Report...';
                
                try {
                    const response = await fetch(`${API_BASE_URL}/report/weekly`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
                    if (!response.ok) throw new Error((await response.json()).error);
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement("a");
                    const disposition = response.headers.get('content-disposition');
                    let filename = "weekly-report.pdf";
                    if (disposition) {
                        const match = /filename="?([^"]+)"?/.exec(disposition);
                        if (match) filename = match[1];
                    }
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                    showMessage("Report downloaded successfully.");
                } catch (error) {
                    showMessage(error.message, true);
                } finally {
                    downloadBtn.disabled = false;
                    buttonText.textContent = originalText;
                }
            });
        }
    };

    const logout = () => {
        localStorage.removeItem("jwt_token");
        window.location.hash = "#login";
        showMessage("You have been logged out.");
        router();
    };

    logoutButton.addEventListener("click", logout);
    window.addEventListener("hashchange", router);
    router();
});