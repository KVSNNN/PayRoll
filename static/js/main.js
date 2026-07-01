/**
 * PayrollPro - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sidebar toggle
    initSidebar();
    // Initialize datetime display
    updateDateTime();
    setInterval(updateDateTime, 1000);
    // Initialize tooltips
    initTooltips();
    // Auto-dismiss alerts
    autoDismissAlerts();
});


/**
 * Sidebar toggle for mobile
 */
function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const openBtn = document.getElementById('sidebarOpen');
    const closeBtn = document.getElementById('sidebarClose');

    if (openBtn) {
        openBtn.addEventListener('click', function() {
            sidebar.classList.add('show');
            // Create backdrop
            let backdrop = document.querySelector('.sidebar-backdrop');
            if (!backdrop) {
                backdrop = document.createElement('div');
                backdrop.className = 'sidebar-backdrop';
                document.body.appendChild(backdrop);
            }
            backdrop.classList.add('show');
            backdrop.addEventListener('click', closeSidebar);
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeSidebar);
    }

    function closeSidebar() {
        sidebar.classList.remove('show');
        const backdrop = document.querySelector('.sidebar-backdrop');
        if (backdrop) backdrop.classList.remove('show');
    }
}


/**
 * Update datetime display in navbar
 */
function updateDateTime() {
    const el = document.getElementById('currentDateTime');
    if (el) {
        const now = new Date();
        const options = {
            weekday: 'short', day: '2-digit', month: 'short', year: 'numeric',
            hour: '2-digit', minute: '2-digit', hour12: true
        };
        el.textContent = now.toLocaleString('en-IN', options);
    }
}


/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function(el) {
        new bootstrap.Tooltip(el);
    });
}


/**
 * Auto-dismiss alerts after 5 seconds
 */
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            bsAlert.close();
        }, 5000);
    });
}


/**
 * Format number as Indian currency
 */
function formatCurrency(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return '₹0.00';
    return '₹' + num.toLocaleString('en-IN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}


/**
 * Salary form auto-calculations
 */
function initSalaryCalculations() {
    const monthlySalary = document.getElementById('hidden-monthly-salary');
    const workingDays = document.getElementById('salary-working-days');
    const presentDays = document.getElementById('salary-present-days');
    const deduction = document.getElementById('salary-deduction');
    const paidAmount = document.getElementById('salary-paid-amount');

    // Display fields
    const absentDisplay = document.getElementById('calc-absent-days');
    const earnedDisplay = document.getElementById('calc-salary-earned');
    const netDisplay = document.getElementById('calc-net-salary');
    const balanceDisplay = document.getElementById('calc-balance');

    function calculate() {
        if (!monthlySalary) return;

        const salary = parseFloat(monthlySalary.value) || 0;
        const total = parseInt(workingDays.value) || 30;
        const present = parseInt(presentDays.value) || 0;
        const deductionAmt = parseFloat(deduction.value) || 0;
        const paid = parseFloat(paidAmount.value) || 0;

        const absent = Math.max(0, total - present);
        const dailyRate = total > 0 ? salary / total : 0;
        const earned = Math.round(dailyRate * present * 100) / 100;
        const net = Math.max(0, earned - deductionAmt);
        const balance = Math.max(0, net - paid);

        if (absentDisplay) absentDisplay.textContent = absent;
        if (earnedDisplay) earnedDisplay.textContent = formatCurrency(earned);
        if (netDisplay) netDisplay.textContent = formatCurrency(net);
        if (balanceDisplay) balanceDisplay.textContent = formatCurrency(balance);
    }

    // Attach listeners
    [workingDays, presentDays, deduction, paidAmount].forEach(function(el) {
        if (el) {
            el.addEventListener('input', calculate);
            el.addEventListener('change', calculate);
        }
    });

    // Initial calculation
    calculate();
}


/**
 * Employee selection handler for salary form
 */
function initEmployeeSelect() {
    const employeeSelect = document.getElementById('salary-employee');
    if (!employeeSelect) return;

    employeeSelect.addEventListener('change', function() {
        const employeeId = this.value;
        if (!employeeId) return;

        fetch(`/salary/get-employee-salary/?employee_id=${employeeId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const hiddenSalary = document.getElementById('hidden-monthly-salary');
                    const salaryDisplay = document.getElementById('display-monthly-salary');
                    if (hiddenSalary) hiddenSalary.value = data.monthly_salary;
                    if (salaryDisplay) salaryDisplay.textContent = formatCurrency(data.monthly_salary);
                    // Trigger recalculation
                    initSalaryCalculations();
                }
            })
            .catch(err => console.error('Error fetching employee salary:', err));
    });
}


/**
 * Confirm action dialog
 */
function confirmAction(message) {
    return confirm(message || 'Are you sure you want to proceed?');
}


/**
 * Print page
 */
function printPage() {
    window.print();
}
