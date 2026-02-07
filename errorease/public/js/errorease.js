// apps/erpoease/errorease/public/js/errorease.js

// ULTIMATE FIX: Intercept ALL Frappe error displays
(function () {
    if (!window.frappe) {
        console.warn("ErrorEase: Frappe not available");
        return;
    }
    console.log("ErrorEase: Starting ULTIMATE initialization...");
    
    // Store originals
    window._originalMsgprint = frappe.msgprint;
    window._originalThrow = frappe.throw;
    window._lastErrorEaseError = null;
    window._errorDialogShown = false;
    
    // ========== CRITICAL: Patch frappe.throw FIRST ==========
    if (frappe.throw && typeof frappe.throw === 'function') {
        frappe.throw = function (message, title = "Error", indicator = "red") {
            console.log("✓ ErrorEase: frappe.throw INTERCEPTED:", message.substring(0, 200));

            // Store error IMMEDIATELY
            window._lastErrorEaseError = {
                message: message,
                title: title,
                timestamp: Date.now(),
                source: 'throw'
            };

            // Mark that error is happening
            window._errorDialogShown = true;

            // Call original
            const result = window._originalThrow.call(this, message, title, indicator);

            // ULTIMATE FIX: Direct injection after ANY dialog appears
            setTimeout(() => {
                ultimateErrorButtonInjection(message, title);
            }, 100);

            return result;
        };
        console.log("✓ ErrorEase: frappe.throw ULTRA-PATCHED");
    }
    
    // ========== ALSO patch msgprint ==========
    if (frappe.msgprint && typeof frappe.msgprint === 'function') {
        frappe.msgprint = function (opts, ...args) {
            const result = window._originalMsgprint.call(this, opts, ...args);

            let isError = false;
            let errorMessage = '';
            let errorTitle = '';

            // ULTIMATE detection: ANYTHING that looks like error
            if (typeof opts === 'object') {
                errorMessage = opts.message || opts.title || '';
                errorTitle = opts.title || '';

                // Check EVERY possible error indicator
                isError =
                    opts.indicator === 'red' ||
                    opts.indicator === 'orange' ||
                    (errorTitle && errorTitle.toLowerCase().includes('error')) ||
                    (errorMessage && errorMessage.toLowerCase().includes('error')) ||
                    (errorTitle && errorTitle.toLowerCase().includes('server')) ||
                    (errorMessage && errorMessage.toLowerCase().includes('exception')) ||
                    (errorMessage && errorMessage.toLowerCase().includes('traceback')) ||
                    (errorMessage && errorMessage.toLowerCase().includes('nameerror')) ||
                    (errorMessage && errorMessage.toLowerCase().includes('typeerror'));

            } else if (typeof opts === 'string') {
                const lowerOpts = opts.toLowerCase();
                isError =
                    lowerOpts.includes('error') ||
                    lowerOpts.includes('exception') ||
                    lowerOpts.includes('traceback');
                errorMessage = opts;
            }

            // Also check args
            if (args[0] && typeof args[0] === 'object') {
                const arg = args[0];
                if (arg.indicator === 'red' || arg.indicator === 'orange') {
                    isError = true;
                }
                if (arg.title && arg.title.toLowerCase().includes('error')) {
                    isError = true;
                    errorTitle = arg.title;
                }
            }

            if (isError && errorMessage) {
                console.log("✓ ErrorEase: msgprint error detected:", errorTitle || errorMessage.substring(0, 100));

                window._lastErrorEaseError = {
                    message: errorMessage,
                    title: errorTitle,
                    timestamp: Date.now(),
                    source: 'msgprint'
                };
                window._errorDialogShown = true;

                setTimeout(() => {
                    ultimateErrorButtonInjection(errorMessage, errorTitle);
                }, 100);
            }

            return result;
        };
        console.log("✓ ErrorEase: msgprint ULTRA-PATCHED");
    }
    
    // ========== NUCLEAR OPTION: Direct DOM Observer ==========
    const observer = new MutationObserver((mutations) => {
        if (window._errorDialogShown) return;

        for (const mutation of mutations) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) {
                        checkAndInject(node);
                    }
                });
            }
            else if (mutation.type === 'attributes') {
                checkAndInject(mutation.target);
            }
        }
    });

    function checkAndInject(node) {
        const dialog = node.classList?.contains('modal-dialog') ? node :
            node.querySelector?.('.modal-dialog, .frappe-dialog, .msgprint-dialog');

        if (dialog) {
            const style = window.getComputedStyle(dialog.closest('.modal') || dialog);
            if (style.display === 'none' || style.visibility === 'hidden') return;

            console.log("ErrorEase Observer: Dialog detected (" + (dialog.className || 'unknown') + ")");

            setTimeout(() => {
                const dialogText = dialog.querySelector('.modal-body')?.textContent.trim() || dialog.textContent.trim();
                const titleEl = dialog.querySelector('.modal-title');
                const titleText = titleEl ? titleEl.textContent : '';

                if (dialogText.toLowerCase().includes('error') ||
                    dialogText.toLowerCase().includes('exception') ||
                    dialogText.toLowerCase().includes('traceback') ||
                    dialogText.toLowerCase().includes('nameerror') ||
                    (titleText && titleText.toLowerCase().includes('error'))) {

                    console.log("ErrorEase Observer: ERROR dialog found!");
                    ultimateErrorButtonInjection(dialogText, titleText || 'Client Error');
                }
            }, 200);
        }
    }

    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['class', 'style'] });
    console.log("✓ ErrorEase: DOM Observer started");

    // ========== FALLBACK: Persistent Poller ==========
    setInterval(() => {
        const visibleDialogs = Array.from(document.querySelectorAll('.modal-dialog, .msgprint-dialog, .frappe-dialog')).filter(d => {
            const style = window.getComputedStyle(d.closest('.modal') || d);
            return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0';
        });

        visibleDialogs.forEach(dialog => {
            if (dialog.querySelector('.errorease-btn')) return;

            const dialogText = dialog.querySelector('.modal-body')?.textContent.trim() || dialog.textContent.trim();
            const title = dialog.querySelector('.modal-title')?.textContent || '';

            const isClientScript = dialogText.includes('Error in Client Script') || title.includes('Client Script');
            const isGenericError = dialogText.toLowerCase().includes('error') || title.toLowerCase().includes('error');

            if (isClientScript || isGenericError) {
                ultimateErrorButtonInjection(dialogText, title || 'Polled Error');
            }
        });
    }, 1000);

    console.log("✓ ErrorEase: ULTIMATE initialization complete");
})();

// ULTIMATE Button Injection - WORKS FOR ALL DIALOGS
function ultimateErrorButtonInjection(errorMessage, errorTitle = '', targetDialog = null) {
    console.log("ULTIMATE: Attempting button injection...");

    let attempts = 0;
    const maxAttempts = 15;
    const interval = 200;

    function attempt() {
        attempts++;

        try {
            let dialog = targetDialog;

            if (!dialog) {
                const dialogs = document.querySelectorAll('.modal-dialog, .msgprint-dialog, .frappe-dialog');

                if (dialogs.length === 0) {
                    if (attempts < maxAttempts) {
                        setTimeout(attempt, interval);
                    } else {
                        console.log("ULTIMATE: No dialogs found after", maxAttempts, "attempts");
                    }
                    return;
                }
                dialog = dialogs[dialogs.length - 1];
            }

            const dialogText = dialog.querySelector('.modal-body')?.textContent.trim() || dialog.textContent.trim();
            const title = dialog.querySelector('h4.modal-title')?.textContent || errorTitle || '';

            // ABORT if this is our own explanation dialog
            if (title.includes('Error Explanation') || title.includes('AI Error Explanation')) {
                console.log("ULTIMATE: Skipping explanation dialog");
                return;
            }

            const fullText = dialog.textContent;
            const isClientScriptError = fullText.includes('Error in Client Script') ||
                (title && title.includes('Client Script'));

            const errorKeywords = [
                'error', 'exception', 'traceback', 'failure', 'failed',
                'validation', 'mandatory', 'permission', 'forbidden',
                'does not exist', 'duplicate', 'data error', 'integrity',
                'syntax', 'link validation', 'implicit commit',
                'reference', 'type', 'network', 'timeout', 'connection',
                'not found', 'session expired', 'cache',
                'stock', 'accounting', 'workflow', 'print format'
            ];

            const dialogContentLower = dialogText.toLowerCase();
            const dialogTitleLower = (title || '').toLowerCase();

            const isGenericError = errorKeywords.some(keyword =>
                dialogContentLower.includes(keyword) || dialogTitleLower.includes(keyword)
            );

            if (!isGenericError && !isClientScriptError) {
                if (!targetDialog && attempts < maxAttempts) {
                    setTimeout(attempt, interval);
                }
                return;
            }

            console.log("ULTIMATE: Confirmed error dialog (ClientScript: " + isClientScriptError + "), injecting button...");

            if (forceInjectButton(dialog, errorMessage)) {
                console.log("✓ ULTIMATE: Button injected SUCCESSFULLY on attempt", attempts);
                window._errorDialogShown = false;
            } else {
                if (attempts < maxAttempts) {
                    setTimeout(attempt, interval);
                }
            }

        } catch (error) {
            console.error("ULTIMATE injection error:", error);
            if (attempts < maxAttempts) {
                setTimeout(attempt, interval);
            }
        }
    }

    setTimeout(attempt, 100);
}

// ========== CRITICAL FIX: Updated forceInjectButton function ==========
function forceInjectButton(dialog, errorMessage) {
    try {
        // ========== FIX 1: Check if modal-footer is hidden ==========
        let footer = dialog.querySelector('.modal-footer, .msgprint-footer, .dialog-footer');
        
        // If footer exists but is hidden (has 'hide' class or display:none)
        if (footer) {
            const footerStyle = window.getComputedStyle(footer);
            const hasHideClass = footer.classList.contains('hide');
            const isDisplayNone = footerStyle.display === 'none';
            
            if (hasHideClass || isDisplayNone) {
                console.log("ULTIMATE: Footer is hidden, will use modal-body instead");
                footer = null; // Force use of modal-body
            }
        }
        
        // ========== FIX 2: Use modal-body if footer is hidden or doesn't exist ==========
        if (!footer) {
            // Try to use modal-body instead
            footer = dialog.querySelector('.modal-body');
            
            if (footer) {
                console.log("ULTIMATE: Using modal-body instead of hidden footer");
                // Create a wrapper inside modal-body for our button
                const buttonWrapper = document.createElement('div');
                buttonWrapper.className = 'errorease-button-wrapper';
                buttonWrapper.style.cssText = 'padding: 15px 0; text-align: center; border-top: 1px solid #e5e7eb; margin-top: 15px; display: block !important;';
                footer.appendChild(buttonWrapper);
                footer = buttonWrapper;
            } else {
                // Create footer as last resort
                const modalContent = dialog.querySelector('.modal-content');
                if (modalContent) {
                    footer = document.createElement('div');
                    footer.className = 'modal-footer errorease-forced-footer';
                    footer.style.cssText = 'padding: 15px; border-top: 1px solid #e5e7eb; text-align: center; background: #f9fafb; display: block !important;';
                    modalContent.appendChild(footer);
                    console.log("ULTIMATE: Created forced footer!");
                }
            }
        }
        
        // ========== FIX 3: FORCE footer to be visible ==========
        if (footer) {
            // Remove 'hide' class if present
            footer.classList.remove('hide');
            // Force display
            footer.style.display = 'block';
            footer.style.visibility = 'visible';
            footer.style.opacity = '1';
        }

        if (!footer) {
            console.log("ULTIMATE: Could not find or create footer container");
            return false;
        }

        // Skip if button already exists
        if (footer.querySelector('.errorease-btn')) {
            return true;
        }

        // Get error message
        if (!errorMessage || errorMessage.trim() === '') {
            const messageEl = dialog.querySelector('.modal-body, .msgprint-message, [class*="message"]');
            if (messageEl) {
                errorMessage = messageEl.textContent.trim();
            } else {
                errorMessage = dialog.textContent.substring(0, 300);
            }
        }

        // Create button
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn btn-xs btn-primary errorease-btn';
        btn.innerHTML = '<i class="fa fa-robot" style="margin-right: 5px"></i> Explain Error';

        // FORCE visibility with aggressive styling
        btn.style.cssText = `
            margin: 10px !important;
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
            border: 2px solid #1e7e34 !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 6px !important;
            padding: 8px 16px !important;
            font-size: 13px !important;
            line-height: 18px !important;
            min-height: 36px !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 3px 6px rgba(0,0,0,0.16) !important;
            cursor: pointer !important;
            transition: all 0.3s !important;
            opacity: 1 !important;
            visibility: visible !important;
            z-index: 9999 !important;
            position: relative !important;
        `;

        // Hover effects
        btn.addEventListener('mouseenter', () => {
            btn.style.background = 'linear-gradient(135deg, #218838 0%, #1ba87e 100%) !important';
            btn.style.borderColor = '#1c7430 !important';
            btn.style.transform = 'translateY(-2px) !important';
            btn.style.boxShadow = '0 6px 12px rgba(0,0,0,0.2) !important';
        });

        btn.addEventListener('mouseleave', () => {
            btn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%) !important';
            btn.style.borderColor = '#1e7e34 !important';
            btn.style.transform = 'translateY(0) !important';
            btn.style.boxShadow = '0 3px 6px rgba(0,0,0,0.16) !important';
        });

        // Click handler
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();

            if (!errorMessage || errorMessage.trim() === '') {
                frappe.show_alert({
                    message: __('No error message found'),
                    indicator: 'orange'
                });
                return;
            }

            // Disable button while analyzing
            const originalHTML = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = '<i class="fa fa-spinner fa-spin" style="margin-right: 5px"></i> Analyzing...';
            btn.style.opacity = '0.7';

            // Get current context
            const currentRoute = frappe.get_route ? frappe.get_route() : [];

            // Clean error message
            let cleanMessage = errorMessage;
            const bodyElement = dialog.querySelector('.modal-body');
            if (bodyElement) {
                const lines = bodyElement.textContent.split('\n').map(l => l.trim()).filter(Boolean);
                const tbIndex = lines.findIndex(l => l.includes('Traceback') || l.includes('Error:'));
                if (tbIndex >= 0) {
                    cleanMessage = lines.slice(tbIndex).join('\n');
                } else {
                    cleanMessage = bodyElement.textContent.trim();
                }
            }

            // Append extra context
            cleanMessage += `\n\nContext: ${currentRoute[1] || 'Unknown'} form, Before Save event, Server Script error`;

            // Call API
            frappe.call({
                method: "errorease.api.explain_error",
                args: {
                    message: cleanMessage,
                    doctype: (currentRoute[0] === 'Form' || currentRoute[0] === 'List') ? currentRoute[1] : null,
                    docname: currentRoute[2] || null,
                    route: currentRoute.join('/') || null
                },
                callback: (response) => {
                    btn.disabled = false;
                    btn.innerHTML = originalHTML;
                    btn.style.opacity = '1';

                    if (response && response.message && response.message.explanation) {
                        window.ErrorEase.showExplanation(response.message.explanation, response.message.cached);
                    } else {
                        frappe.show_alert({
                            message: __('Failed to get explanation.'),
                            indicator: 'red'
                        });
                    }
                },
                error: () => {
                    btn.disabled = false;
                    btn.innerHTML = originalHTML;
                    btn.style.opacity = '1';

                    frappe.show_alert({
                        message: __('ErrorEase service unavailable.'),
                        indicator: 'red'
                    });
                }
            });
        });

        // ========== FIX 4: Always append to container ==========
        footer.appendChild(btn);
        console.log("ULTIMATE: Button appended to footer/container");

        // Add pulsating animation
        btn.style.animation = 'errorease-pulse 2s infinite';

        return true;

    } catch (error) {
        console.error("ULTIMATE force injection failed:", error);
        return false;
    }
}

 
// ErrorEase Core
 
window.ErrorEase = {
    showExplanation: function (explanation, cached = false) {
        // Remove unwanted sections
        explanation = explanation.replace(/💡\s*Prevention Tips[:\s\S]*/gi, '');
        explanation = explanation.replace(/Prevention Tips[:\s\S]*/gi, '');
        explanation = explanation.replace(/Tips[:\s\S]*/gi, '');
        explanation = explanation.replace(/Best Practices[:\s\S]*/gi, '');

        const formattedExplanation = this.formatExplanation(explanation);

        const dialog = new frappe.ui.Dialog({
            title: cached
                ? '<i class="fa fa-bolt text-warning" style="margin-right:8px"></i> Error Explanation (Cached)'
                : '<i class="fa fa-robot text-primary" style="margin-right:8px"></i> AI Error Explanation',
            size: 'large',
            fields: [{
                fieldname: 'explanation',
                fieldtype: 'HTML',
                options: formattedExplanation
            }],
            primary_action_label: '<i class="fa fa-times"></i> Close',
            primary_action: () => dialog.hide()
        });

        dialog.$wrapper.addClass('errorease-explanation-dialog');
        dialog.show();
    },

    formatExplanation: function (explanation) {
        let text = (explanation || '').toString();
        text = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').trim();

        const problemMatch = text.match(/What Went Wrong[:\s]*(.*?)(?=(How to Fix It|$))/is);
        const solutionMatch = text.match(/How to Fix It[:\s]*(.*)/is);

        let problem = problemMatch ? problemMatch[1].trim() : '';
        let solution = solutionMatch ? solutionMatch[1].trim() : '';

        if (!problem && text) {
            const numStart = text.search(/\d+\.\s/);
            if (numStart >= 0) {
                problem = text.substring(0, numStart).trim();
                solution = text.substring(numStart).trim();
            } else {
                problem = text;
            }
        }

        const escapeHtml = (s) => {
            if (!s) return '';
            return String(s)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#039;')
                .replace(/\n/g, '<br>');
        };

        const formatSolution = (sol) => {
            if (!sol) return '<p>No steps provided.</p>';

            const lines = sol.split('\n').map(l => l.trim()).filter(Boolean);
            if (lines.length === 0) return '<p>No steps provided.</p>';

            let html = '<ol style="margin-left: 20px; padding-left: 0;">';

            lines.forEach(line => {
                const numberedMatch = line.match(/^(\d+\.|•|-)\s*(.*)/);
                if (numberedMatch) {
                    html += '<li style="margin-bottom: 8px; line-height: 1.5;">' + escapeHtml(numberedMatch[2]) + '</li>';
                } else {
                    html += '<li style="margin-bottom: 8px; line-height: 1.5;">' + escapeHtml(line) + '</li>';
                }
            });

            html += '</ol>';
            return html;
        };

        const problemHtml = '<div style="background: #fff5f5; border-left: 4px solid #dc3545; padding: 12px 15px; border-radius: 0 4px 4px 0; margin-bottom: 20px; line-height: 1.6;">' +
            escapeHtml(problem) + '</div>';
        const solutionHtml = formatSolution(solution);

        return '<div style="padding: 20px; background: #fbfdff; border-radius: 10px; border-left: 5px solid #3b82f6; line-height: 1.6;">' +
            '<h3 style="color: #dc3545; margin-bottom: 10px; font-size: 16px; font-weight: 600;">' +
            '<i class="fa fa-exclamation-triangle" style="margin-right:8px"></i> What Went Wrong' +
            '</h3>' +
            problemHtml +
            '<h3 style="color: #28a745; margin-bottom: 10px; font-size: 16px; font-weight: 600;">' +
            '<i class="fa fa-wrench" style="margin-right:8px"></i> How to Fix It' +
            '</h3>' +
            solutionHtml +
            '</div>';
    },

    test: function () {
        console.log("ErrorEase: Testing...");
        frappe.throw("Test error for ErrorEase - should show Explain Error button NOW");
    },

    debug: function () {
        console.log("=== ErrorEase Debug ===");
        console.log("Last error:", window._lastErrorEaseError);
        console.log("Error dialog shown flag:", window._errorDialogShown);

        const dialogs = document.querySelectorAll('.modal-dialog, .msgprint-dialog');
        console.log("Dialogs found:", dialogs.length);
        dialogs.forEach((d, i) => {
            console.log(`Dialog ${i}:`, {
                hasFooter: !!d.querySelector('.modal-footer'),
                footerHidden: d.querySelector('.modal-footer')?.classList.contains('hide'),
                hasOurButton: !!d.querySelector('.errorease-btn'),
                title: d.querySelector('.modal-title')?.textContent,
                text: d.textContent.substring(0, 100)
            });
        });
    }
};

 
// ULTIMATE CSS - Force button visibility
(function () {
    const style = document.createElement('style');
    style.textContent = `
        .errorease-btn {
            display: inline-flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 9999 !important;
            position: relative !important;
        }
        
        /* FIX: Remove hide class from modal-footer when we add our button */
        .modal-footer:has(.errorease-btn) {
            display: block !important;
        }
        .modal-footer.hide:has(.errorease-btn) {
            display: block !important;
        }
        
        @keyframes errorease-pulse {
            0% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
            100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }
        }
        
        .errorease-forced-footer {
            padding: 15px !important;
            border-top: 1px solid #e5e7eb !important;
            text-align: center !important;
            background: #f9fafb !important;
            display: block !important;
        }
        
        .errorease-button-wrapper {
            padding: 15px 0 !important;
            text-align: center !important;
            border-top: 1px solid #e5e7eb !important;
            margin-top: 15px !important;
            display: block !important;
        }
        
        .errorease-explanation-dialog .modal-body {
            max-height: 70vh;
            overflow-y: auto;
        }
    `;
    document.head.appendChild(style);
    console.log("✓ ErrorEase: ULTIMATE CSS loaded");
})();

// Initialize
if (window.frappe && frappe.ready) {
    frappe.ready(() => {
        console.log("✓ ErrorEase: ULTRA-READY");
    });
} else {
    setTimeout(() => {
        console.log("✓ ErrorEase: ULTRA-LOADED");
    }, 1000);
}

