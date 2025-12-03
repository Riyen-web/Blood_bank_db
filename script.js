

document.addEventListener('DOMContentLoaded', () => {
    const API_BASE_URL = '/api';
    // Re-added global data arrays
    let ALL_ROLES = [], ALL_TASKS = [], ALL_STAFF = [], ALL_DONORS = [], CURRENT_STAFF = null;

    const navButtons = document.querySelectorAll('nav button');
    const views = document.querySelectorAll('.view');
    const statusMessageDiv = document.getElementById('status-message');
    const addStaffModal = document.getElementById('add-staff-modal');

    // --- Utility Functions ---

    function formatDonorId(id) { return `D${String(id).padStart(4, '0')}`; }
    function formatStaffId(id) { return `S${String(id).padStart(4, '0')}`; }
    function formatUnitId(id) { return `U${String(id).padStart(4, '0')}`; }

    function populateStaffDropdown(select, list, roleName = null) {
        select.innerHTML = `<option value="" disabled selected>-- Select Staff --</option>`;
        const filteredList = roleName ? list.filter(s => s.role_name === roleName) : list;
        filteredList.forEach(s => {
            select.innerHTML += `<option value="${s.staff_id}">${s.first_name} ${s.last_name} (${formatStaffId(s.staff_id)} - ${s.role_name})</option>`;
        });
    }

    function populateDonorDropdown(select, list) {
        select.innerHTML = `<option value="" disabled selected>-- Select Donor --</option>`;
        list.forEach(d => {
            select.innerHTML += `<option value="${d.donor_id}">${d.first_name} ${d.last_name} (${formatDonorId(d.donor_id)})</option>`;
        });
    }
    
    // New function to populate the Unit ID dropdown for Inventory
    async function populateInventoryDropdown() {
        const select = document.getElementById('inventory-unit-id');
        select.innerHTML = `<option value="" disabled selected>-- Select Unit to Update --</option>`;
        try {
            const list = await apiFetch('/inventory'); // Fetch latest inventory
            list.forEach(u => {
                select.innerHTML += `<option value="${u.unit_id}">${formatUnitId(u.unit_id)} (${u.blood_type}) - ${u.status}</option>`;
            });
        } catch(error) { /* Handle error silently or show message */ }
    }

    // New function to load all necessary data once or on demand
    async function loadInitialDataForForms() {
        try {
            // Fetch staff and roles (needed for screening, collection, staff management)
            const [staff, roles, tasks] = await Promise.all([
                apiFetch('/staff'), 
                apiFetch('/roles'), 
                apiFetch('/tasks')
            ]);
            ALL_STAFF = staff;
            ALL_ROLES = roles;
            ALL_TASKS = tasks;

            // Populate Dropdowns that rely on this data
            populateStaffDropdown(document.getElementById('screening-staff-id'), ALL_STAFF);
            populateStaffDropdown(document.getElementById('collection-staff-id'), ALL_STAFF, 'Phlebotomist'); // Assuming 'Phlebotomist' is a role name
            populateRoleDropdown(document.getElementById('staff-role-id'), ALL_ROLES);
            document.getElementById('staff-details-role-id') && populateRoleDropdown(document.getElementById('staff-details-role-id'), ALL_ROLES);
            
            // Populate inventory dropdown separately as it changes frequently
            populateInventoryDropdown(); 

        } catch (error) { 
            console.error("Could not load initial data for forms", error); 
        }
    }
    
    // --- Navigation and View Management ---

    function showView(viewId) {
        views.forEach(v => v.classList.remove('active'));
        navButtons.forEach(b => b.classList.remove('active'));
        document.getElementById(viewId)?.classList.add('active');
        document.querySelector(`nav button[data-view-id="${viewId}"]`)?.classList.add('active');
        statusMessageDiv.style.display = 'none';

        // Conditional data loading based on the view
        if (viewId === 'staff-view') {
            initializeStaffManagement();
        } else if (['screening-view', 'collection-view', 'inventory-view'].includes(viewId)) {
            // Load staff/roles/inventory data when switching to these views
            loadInitialDataForForms();
        }
        
        // Reset forms specific to the current workflow
        if (viewId !== 'screening-view' && viewId !== 'collection-view') {
            screeningForm.style.display = 'none';
            screeningSearchResults.innerHTML = '';
            document.getElementById('screening-search-form')?.reset();
        }
    }
    navButtons.forEach(button => button.addEventListener('click', () => showView(button.dataset.viewId)));

    // ... (showStatusMessage and apiFetch functions remain the same) ...
    function showStatusMessage(message, type) {
        statusMessageDiv.textContent = message;
        statusMessageDiv.className = type;
        statusMessageDiv.style.display = 'block';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    async function apiFetch(endpoint, method = 'GET', body = null) {
        const options = { method, headers: { 'Content-Type': 'application/json' } };
        if (body) options.body = JSON.stringify(body);
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || `HTTP error! Status: ${response.status}`);
            return result;
        } catch (error) {
            showStatusMessage(error.message, 'error');
            throw error;
        }
    }
    
    // --- Donor Registration ---
    document.getElementById('donor-registration-form').addEventListener('submit', async e => {
        e.preventDefault();
        try {
            const result = await apiFetch('/donors', 'POST', { 
                first_name: e.target.elements['reg-first-name'].value, 
                last_name: e.target.elements['reg-last-name'].value, 
                date_of_birth: e.target.elements['reg-dob'].value, 
                gender: e.target.elements['reg-gender'].value, 
                blood_group: e.target.elements['reg-blood-group'].value, 
                phone_number: e.target.elements['reg-phone'].value, 
                email: e.target.elements['reg-email'].value 
            });
            showStatusMessage(result.message, 'success');
            e.target.reset();
        } catch (error) {}
    });
// --- ADD to script.js ---

document.getElementById('organization-registration-form').addEventListener('submit', async e => {
    e.preventDefault();
    
    // Validate email field for optional input
    const emailValue = document.getElementById('org-reg-email').value.trim();
    const email = emailValue || null; 

    try {
        const result = await apiFetch('/organizations', 'POST', {
            name: document.getElementById('org-reg-name').value,
            org_type: document.getElementById('org-reg-type').value,
            contact_person: document.getElementById('org-reg-contact-person').value,
            contact_phone: document.getElementById('org-reg-phone').value,
            contact_email: email
        });
        
        showStatusMessage(result.message, 'success');
        e.target.reset();
        
        // Optional: Reload organization data globally after successful registration
        loadOrganizations();

    } catch (error) {
        // Error already handled by apiFetch
    }
});
    // --- Donor Search (General) ---
    document.getElementById('donor-search-form').addEventListener('submit', async e => {
        e.preventDefault();
        const lastName = document.getElementById('search-last-name').value;
        const container = document.getElementById('donor-search-results');
        container.innerHTML = `<p>Searching...</p>`;
        try {
            const donors = await apiFetch(`/donors/search?last_name=${encodeURIComponent(lastName)}`);
            container.innerHTML = donors.length ? '' : `<p>No donors found.</p>`;
            donors.forEach(d => { container.innerHTML += `<div class="result-card"><strong>Name:</strong> ${d.first_name} ${d.last_name}<br><strong>Blood Type:</strong> ${d.blood_type}<br><small>ID: ${formatDonorId(d.donor_id)}</small></div>`; });
        } catch (error) { container.innerHTML = `<p>Error fetching donors.</p>`; }
    });
    
    // --- Screening Workflow (Start) ---
    const screeningSearchForm = document.getElementById('screening-search-form');
    const screeningSearchResults = document.getElementById('screening-search-results');
    const screeningForm = document.getElementById('screening-form');

    screeningSearchForm.addEventListener('submit', async e => {
        e.preventDefault();
        const lastName = document.getElementById('screening-search-lastname').value;
        screeningSearchResults.innerHTML = `<p>Searching...</p>`;
        screeningForm.style.display = 'none';
        try {
            const donors = await apiFetch(`/donors/search?last_name=${encodeURIComponent(lastName)}`);
            screeningSearchResults.innerHTML = donors.length ? '' : `<p>No donors found.</p>`;
            donors.forEach(d => {
                const card = document.createElement('div');
                card.className = 'result-card';
                card.innerHTML = `<div><strong>Name:</strong> ${d.first_name} ${d.last_name}<br><small>ID: ${formatDonorId(d.donor_id)}</small></div>`;
                
                // *** Logic to select the donor for screening ***
                card.onclick = () => {
                    document.getElementById('screening-donor-id').value = d.donor_id;
                    document.getElementById('screening-donor-name').textContent = `Screening Vitals for: ${d.first_name} ${d.last_name} (${d.blood_type})`;
                    // Store blood group for later collection step
                    document.getElementById('screening-donor-blood-type').value = d.blood_type; 
                    
                    screeningForm.style.display = 'grid';
                    screeningSearchResults.innerHTML = '';
                    screeningSearchForm.reset();
                };
                screeningSearchResults.appendChild(card);
            });
        } catch (error) { screeningSearchResults.innerHTML = `<p>Error fetching donors.</p>`; }
    });

    // --- Screening Workflow (Submission) ---
    screeningForm.addEventListener('submit', async e => { 
        e.preventDefault(); 
        try { 
            const result = await apiFetch('/screenings', 'POST', { 
                donor_id: document.getElementById('screening-donor-id').value, 
                staff_id: document.getElementById('screening-staff-id').value, 
                hemoglobin: document.getElementById('screening-hemoglobin').value, 
                bp_systolic: document.getElementById('screening-systolic').value, 
                bp_diastolic: document.getElementById('screening-diastolic').value, 
                weight_kg: document.getElementById('screening-weight').value, 
                notes: document.getElementById('screening-notes').value 
            }); 
            
            showStatusMessage(`${result.message}. Reason: ${result.notes}`, result.is_eligible ? 'success' : 'error'); 
            
            if (result.is_eligible) {
                 // ** AUTOMATICALLY TRANSITION TO COLLECTION AND PRE-FILL **
                const donorId = document.getElementById('screening-donor-id').value;
                const bloodGroup = document.getElementById('screening-donor-blood-type').value;

                setTimeout(() => { 
                    showView('collection-view'); 
                    // Pre-fill fields for the collection form
                    // Note: You need ALL_DONORS data loaded to populate the collection dropdown
                    if (ALL_DONORS.length === 0) {
                         // Fallback or ensure ALL_DONORS is loaded in loadInitialDataForForms
                    }
                    
                    // Set the donor ID (must match an option value)
                    document.getElementById('collection-donor-id').value = donorId; 
                    
                    document.getElementById('collection-screening-id').value = result.screening_id;
                    document.getElementById('collection-blood-group').value = bloodGroup;
                    document.getElementById('collection-screening-id').readOnly = true; // Lock the screening ID
                    document.getElementById('collection-blood-group').readOnly = true; // Lock the blood group
                }, 1500);
            }
            
            e.target.reset(); 
            screeningForm.style.display = 'none'; 

        } catch (error) {} 
    });

    // --- Collection Submission ---
    document.getElementById('collection-form').addEventListener('submit', async e => { 
        e.preventDefault(); 
        try { 
            const result = await apiFetch('/donations', 'POST', { 
                donor_id: document.getElementById('collection-donor-id').value, 
                screening_id: document.getElementById('collection-screening-id').value, 
                staff_id: document.getElementById('collection-staff-id').value, 
                blood_group: document.getElementById('collection-blood-group').value 
            }); 
            showStatusMessage(`Success! New Unit ID: ${formatUnitId(result.unit_id)}`, 'success'); 
            e.target.reset(); 
            // Refresh inventory dropdown after a new unit is created
            populateInventoryDropdown(); 
        } catch (error) {} 
    });

    // --- Inventory Update ---
    document.getElementById('inventory-update-form').addEventListener('submit', async e => { 
        e.preventDefault(); 
        const unitId = document.getElementById('inventory-unit-id').value; 
        const newStatus = document.getElementById('inventory-new-status').value; 
        try { 
            const result = await apiFetch(`/inventory/${unitId}`, 'PUT', { status: newStatus }); 
            showStatusMessage(result.message, 'success'); 
            e.target.reset(); 
            // Refresh inventory dropdown after status change
            populateInventoryDropdown(); 
        } catch (error) {} 
    });
    
    // --- Reporting (Inventory) ---
    document.getElementById('generate-report-btn').addEventListener('click', async () => { 
        const reportBody = document.querySelector('#report-table tbody'); 
        reportBody.innerHTML = `<tr><td colspan="3">Generating report...</td></tr>`; 
        try { 
            const reportData = await apiFetch('/reports/inventory'); 
            reportBody.innerHTML = reportData.length ? '' : `<tr><td colspan="3">No inventory data found.</td></tr>`; 
            reportData.forEach(item => { 
                const row = reportBody.insertRow(); 
                row.innerHTML = `<td>${item.blood_type}</td><td>${item.status}</td><td>${item.count}</td>`; 
            }); 
        } catch (error) { reportBody.innerHTML = `<tr><td colspan="3">Error fetching report.</td></tr>`; } 
    });

    // --- Staff Management (Rest remains the same) ---
    // ... (initializeStaffManagement, renderStaffList, loadStaffDetails, populateRoleDropdown, renderTaskLists)
    // ... (Event listeners for staff update, task management, and staff registration modal)
    
    // NOTE: Copy the rest of your staff management logic here...

    function populateRoleDropdown(select, roles) {
        select.innerHTML = '';
        roles.forEach(r => { select.innerHTML += `<option value="${r.role_id}">${r.role_name}</option>`; });
    }

    async function initializeStaffManagement() {
        staffDetailsContainer.style.display = 'none';
        try {
            const [staff, roles, tasks] = await Promise.all([apiFetch('/staff'), apiFetch('/roles'), apiFetch('/tasks')]);
            ALL_ROLES = roles; ALL_TASKS = tasks;
            renderStaffList(staff);
            populateRoleDropdown(document.getElementById('staff-role-id'), ALL_ROLES);
        } catch(error) { staffListContainer.innerHTML = `<p>Error loading staff data.</p>`; }
    }

    function renderStaffList(staffList) {
        staffListContainer.innerHTML = staffList.length ? '' : '<p>No staff members found.</p>';
        staffList.forEach(staff => {
            const card = document.createElement('div');
            card.className = 'staff-list-item';
            card.dataset.staffId = staff.staff_id;
            card.innerHTML = `<strong>${staff.first_name} ${staff.last_name}</strong><br><small>${staff.role_name}</small>`;
            card.addEventListener('click', () => {
                document.querySelectorAll('.staff-list-item').forEach(item => item.classList.remove('selected'));
                card.classList.add('selected');
                loadStaffDetails(staff);
            });
            staffListContainer.appendChild(card);
        });
    }

    async function loadStaffDetails(staff) {
        CURRENT_STAFF = staff;
        staffDetailsContainer.style.display = 'block';
        document.getElementById('staff-details-name').textContent = `${staff.first_name} ${staff.last_name}`;
        document.getElementById('staff-details-employee-number').textContent = `Employee #: ${staff.employee_number}`;
        
        // This line was missing the element ID for UUID/Staff ID, re-add or ignore if unnecessary
        // document.getElementById('staff-details-uuid').textContent = `Staff ID: ${formatStaffId(staff.staff_id)}`;
        
        const roleDropdown = document.getElementById('staff-details-role-id');
        populateRoleDropdown(roleDropdown, ALL_ROLES);
        roleDropdown.value = staff.role_id;
        try {
            const assignedTasks = await apiFetch(`/staff/${staff.staff_id}/tasks`);
            renderTaskLists(assignedTasks);
        } catch (error) { document.getElementById('staff-assigned-tasks-list').innerHTML = '<li>Error loading tasks</li>'; }
    }

    function renderTaskLists(assignedTasks) {
        const assignedList = document.getElementById('staff-assigned-tasks-list');
        const availableList = document.getElementById('staff-available-tasks-list');
        assignedList.innerHTML = ''; availableList.innerHTML = '';
        const assignedTaskIds = new Set(assignedTasks.map(t => t.task_id));
        ALL_TASKS.forEach(task => {
            const li = document.createElement('li');
            if (assignedTaskIds.has(task.task_id)) {
                li.innerHTML = `<span>${task.task_name}</span> <button class="remove-task" data-task-id="${task.task_id}">Remove</button>`;
                assignedList.appendChild(li);
            } else {
                li.innerHTML = `<span>${task.task_name}</span> <button class="assign-task" data-task-id="${task.task_id}">Assign</button>`;
                availableList.appendChild(li);
            }
        });
        if (assignedList.innerHTML === '') assignedList.innerHTML = '<li>No tasks assigned.</li>';
        if (availableList.innerHTML === '') availableList.innerHTML = '<li>All tasks assigned.</li>';
    }
    
    document.getElementById('staff-update-role-form').addEventListener('submit', async e => {
        e.preventDefault();
        if (!CURRENT_STAFF) return;
        const newRoleId = document.getElementById('staff-details-role-id').value;
        try {
            const result = await apiFetch(`/staff/${CURRENT_STAFF.staff_id}`, 'PUT', { role_id: newRoleId });
            showStatusMessage(result.message, 'success');
            initializeStaffManagement();
        } catch (error) {}
    });

    staffDetailsContainer.addEventListener('click', async e => {
        if (e.target?.classList.contains('remove-task')) {
            const taskId = e.target.dataset.taskId;
            try { await apiFetch(`/staff/${CURRENT_STAFF.staff_id}/tasks/${taskId}`, 'DELETE'); loadStaffDetails(CURRENT_STAFF); } catch(error) {}
        }
        if (e.target?.classList.contains('assign-task')) {
            const taskId = e.target.dataset.taskId;
            try { await apiFetch(`/staff/${CURRENT_STAFF.staff_id}/tasks`, 'POST', { task_id: taskId }); loadStaffDetails(CURRENT_STAFF); } catch(error) {}
        }
    });

    document.getElementById('show-add-staff-form-btn').addEventListener('click', () => addStaffModal.style.display = 'flex');
    document.getElementById('cancel-add-staff-btn').addEventListener('click', () => addStaffModal.style.display = 'none');
    document.getElementById('staff-registration-form').addEventListener('submit', async e => {
        e.preventDefault();
        try {
            await apiFetch('/staff', 'POST', { first_name: document.getElementById('staff-first-name').value, last_name: document.getElementById('staff-last-name').value, employee_number: document.getElementById('staff-employee-number').value, role_id: document.getElementById('staff-role-id').value });
            showStatusMessage('Staff member added successfully!', 'success');
            e.target.reset();
            addStaffModal.style.display = 'none';
            initializeStaffManagement();
        } catch(error) {}
    });

    showView('donor-registration-view');
});
// --- ADD to script.js (near loadInitialDataForForms) ---
let ALL_ORGANIZATIONS = [];

async function loadOrganizations() {
    try {
        const orgs = await apiFetch('/organizations');
        ALL_ORGANIZATIONS = orgs;
        
        // You can populate the dropdowns here for the Exchange Hub view, but 
        // we'll defer that until the next step to keep the code organized.
        
    } catch(error) { 
        console.error("Could not load organizations data", error);
    }
}
