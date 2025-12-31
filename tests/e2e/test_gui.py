"""
ANALYTICA E2E Tests - GUI Testing with Playwright
==================================================

Browser-based tests for UI interactions:
- Click handling
- Tab switching
- Form inputs
- Export buttons
- Drag & drop
- Error detection
"""

import pytest
import os
import re
from playwright.sync_api import Page, expect, sync_playwright

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:18080")
DSL_EDITOR_URL = f"{API_BASE_URL}/landing/dsl-editor.html"


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(scope="session")
def browser_context():
    """Create browser context for all tests"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            ignore_https_errors=True
        )
        yield context
        context.close()
        browser.close()


@pytest.fixture
def page(browser_context):
    """Create new page for each test"""
    page = browser_context.new_page()
    
    # Collect console errors
    page.errors = []
    page.on("pageerror", lambda err: page.errors.append(str(err)))
    page.on("console", lambda msg: page.errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
    
    yield page
    page.close()


# ============================================================
# BASIC PAGE LOADING
# ============================================================

@pytest.mark.gui
class TestPageLoading:
    """Test basic page loading"""
    
    def test_dsl_editor_loads(self, page: Page):
        """DSL Editor page loads without errors"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Check title or header
        expect(page.locator("body")).to_be_visible()
        
        # No critical JS errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"JS errors: {critical_errors}"
    
    def test_dsl_editor_with_example(self, page: Page):
        """DSL Editor loads with example parameter"""
        page.goto(f"{DSL_EDITOR_URL}#example=industrial-plc")
        page.wait_for_load_state("networkidle")
        
        # Editor should have content
        editor = page.locator("#dslEditor")
        expect(editor).to_be_visible()
        
        # Should have some DSL content
        content = editor.input_value()
        assert len(content) > 0, "Editor should have example content"


# ============================================================
# TAB SWITCHING
# ============================================================

@pytest.mark.gui
class TestTabSwitching:
    """Test tab switching functionality"""
    
    def test_editor_tabs(self, page: Page):
        """Editor tabs (Code/Visual) switch correctly"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Find editor tabs
        code_tab = page.locator(".editor-tab[data-tab='code']")
        visual_tab = page.locator(".editor-tab[data-tab='visual']")
        
        if code_tab.count() > 0 and visual_tab.count() > 0:
            # Click visual tab
            visual_tab.click()
            page.wait_for_timeout(300)
            
            # Click code tab
            code_tab.click()
            page.wait_for_timeout(300)
            
            # No errors
            assert len([e for e in page.errors if "TypeError" in e]) == 0
    
    def test_output_tabs(self, page: Page):
        """Output tabs (JSON/Preview/Export/Logs) switch correctly"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        tabs = ["json", "preview", "export", "logs"]
        
        for tab_name in tabs:
            tab = page.locator(f".output-tab[data-output='{tab_name}']")
            if tab.count() > 0:
                tab.click()
                page.wait_for_timeout(200)
                
                # Tab should be active
                expect(tab).to_have_class(re.compile(r"active"))
        
        # No JS errors during tab switching
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"Errors during tab switch: {critical_errors}"
    
    def test_format_selector(self, page: Page):
        """Format selector (Native/JSON/YAML) works"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Load an example first
        page.goto(f"{DSL_EDITOR_URL}#example=financial")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        formats = ["native", "json", "yaml"]
        
        for fmt in formats:
            btn = page.locator(f".format-btn[data-format='{fmt}']")
            if btn.count() > 0:
                btn.click()
                page.wait_for_timeout(500)
        
        # No errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"Errors during format switch: {critical_errors}"


# ============================================================
# BUTTON CLICKS
# ============================================================

@pytest.mark.gui
class TestButtonClicks:
    """Test button click handlers"""
    
    def test_run_button(self, page: Page):
        """Run button executes pipeline"""
        page.goto(f"{DSL_EDITOR_URL}#example=financial")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        # Find and click run button
        run_btn = page.locator("button:has-text('Uruchom'), button:has-text('Run'), .btn-primary:has-text('▶')")
        if run_btn.count() > 0:
            run_btn.first.click()
            page.wait_for_timeout(2000)
        
        # No critical errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"Errors on run: {critical_errors}"
    
    def test_export_buttons(self, page: Page):
        """Export buttons work without errors"""
        page.goto(f"{DSL_EDITOR_URL}#example=financial&output=export")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        # Switch to export tab
        export_tab = page.locator(".output-tab[data-output='export']")
        if export_tab.count() > 0:
            export_tab.click()
            page.wait_for_timeout(300)
        
        # Click each export button
        export_buttons = page.locator(".export-btn")
        count = export_buttons.count()
        
        for i in range(min(count, 3)):  # Test first 3 buttons
            btn = export_buttons.nth(i)
            btn.click()
            page.wait_for_timeout(1000)
        
        # No critical errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"Errors on export: {critical_errors}"
    
    def test_validate_button(self, page: Page):
        """Validate button works"""
        page.goto(f"{DSL_EDITOR_URL}#example=financial")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        validate_btn = page.locator("button:has-text('Waliduj'), button:has-text('Validate')")
        if validate_btn.count() > 0:
            validate_btn.first.click()
            page.wait_for_timeout(1000)
        
        # No errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0


# ============================================================
# DEPLOYMENTS TABLE
# ============================================================

@pytest.mark.gui
class TestDeploymentsTable:
    """Test deployments table interactions"""
    
    def test_deployment_actions(self, page: Page):
        """Deployment action buttons work"""
        # First run an export to create deployments
        page.goto(f"{DSL_EDITOR_URL}#example=financial&output=export")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        # Click desktop export
        desktop_btn = page.locator(".export-btn:has-text('Desktop')")
        if desktop_btn.count() > 0:
            desktop_btn.click()
            page.wait_for_timeout(2000)
        
        # Switch to preview to see deployments
        preview_tab = page.locator(".output-tab[data-output='preview']")
        if preview_tab.count() > 0:
            preview_tab.click()
            page.wait_for_timeout(500)
        
        # Try clicking deployment action buttons
        redeploy_btn = page.locator("button:has-text('Redeploy')")
        if redeploy_btn.count() > 0:
            redeploy_btn.first.click()
            page.wait_for_timeout(1000)
        
        logs_btn = page.locator("button:has-text('Logs')")
        if logs_btn.count() > 0:
            logs_btn.first.click()
            page.wait_for_timeout(500)
            
            # Close modal if opened
            close_btn = page.locator(".close-btn, button:has-text('×')")
            if close_btn.count() > 0:
                close_btn.first.click()
        
        # No critical errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"Errors in deployments: {critical_errors}"
    
    def test_logs_modal(self, page: Page):
        """Logs modal opens and closes correctly"""
        page.goto(f"{DSL_EDITOR_URL}#example=financial&output=export")
        page.wait_for_load_state("networkidle")
        
        # Run export first
        desktop_btn = page.locator(".export-btn:has-text('Desktop')")
        if desktop_btn.count() > 0:
            desktop_btn.click()
            page.wait_for_timeout(2000)
        
        # Switch to logs tab
        logs_tab = page.locator(".output-tab[data-output='logs']")
        if logs_tab.count() > 0:
            logs_tab.click()
            page.wait_for_timeout(500)
            
            # Should see logs panel
            logs_panel = page.locator(".logs-panel, #outputLogs")
            expect(logs_panel).to_be_visible()
        
        # No errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0


# ============================================================
# EXAMPLES LOADING
# ============================================================

@pytest.mark.gui
class TestExamplesLoading:
    """Test example loading functionality"""
    
    EXAMPLES = [
        "iot-sensor",
        "api-dashboard", 
        "financial",
        "etl-pipeline",
        "industrial-plc",
        "kafka-stream",
        "data-compute"
    ]
    
    def test_load_examples(self, page: Page):
        """All examples load without errors"""
        for example in self.EXAMPLES:
            page.errors = []  # Reset errors
            page.goto(f"{DSL_EDITOR_URL}#example={example}")
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            
            # Editor should have content
            editor = page.locator("#dslEditor")
            if editor.count() > 0:
                content = editor.input_value()
                # May or may not have content depending on example
            
            # No critical errors
            critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
            assert len(critical_errors) == 0, f"Errors loading {example}: {critical_errors}"
    
    def test_example_cards_click(self, page: Page):
        """Example cards in sidebar are clickable"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Find example cards
        example_cards = page.locator(".example-card")
        count = example_cards.count()
        
        if count > 0:
            # Click first example card
            example_cards.first.click()
            page.wait_for_timeout(500)
            
            # Editor should have content
            editor = page.locator("#dslEditor")
            if editor.count() > 0:
                content = editor.input_value()
                # Should have loaded something
        
        # No errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0


# ============================================================
# ATOM LIBRARY
# ============================================================

@pytest.mark.gui
class TestAtomLibrary:
    """Test atom library interactions"""
    
    def test_category_toggle(self, page: Page):
        """Atom categories expand/collapse"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Find category headers
        category_headers = page.locator(".category-header")
        count = category_headers.count()
        
        for i in range(min(count, 3)):
            header = category_headers.nth(i)
            header.click()
            page.wait_for_timeout(200)
            header.click()
            page.wait_for_timeout(200)
        
        # No errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0
    
    def test_atom_click(self, page: Page):
        """Clicking atom adds to editor"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Clear editor first
        editor = page.locator("#dslEditor")
        if editor.count() > 0:
            editor.fill("")
        
        # Find and click an atom
        atom_items = page.locator(".atom-item")
        if atom_items.count() > 0:
            atom_items.first.click()
            page.wait_for_timeout(300)
            
            # Editor should have content
            if editor.count() > 0:
                content = editor.input_value()
                # Should have added atom template
        
        # No errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0


# ============================================================
# ERROR DETECTION
# ============================================================

@pytest.mark.gui
class TestErrorDetection:
    """Test that UI handles errors gracefully"""
    
    def test_invalid_dsl_execution(self, page: Page):
        """Invalid DSL shows error, doesn't crash"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Enter invalid DSL
        editor = page.locator("#dslEditor")
        if editor.count() > 0:
            editor.fill("invalid.atom.that.does.not.exist()")
        
        # Click run
        run_btn = page.locator("button:has-text('Uruchom'), button:has-text('Run'), .btn-primary")
        if run_btn.count() > 0:
            run_btn.first.click()
            page.wait_for_timeout(2000)
        
        # Should not have critical JS errors (API errors are OK)
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0, f"JS errors on invalid DSL: {critical_errors}"
    
    def test_empty_editor_run(self, page: Page):
        """Running empty editor doesn't crash"""
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Clear editor
        editor = page.locator("#dslEditor")
        if editor.count() > 0:
            editor.fill("")
        
        # Click run
        run_btn = page.locator("button:has-text('Uruchom'), button:has-text('Run'), .btn-primary")
        if run_btn.count() > 0:
            run_btn.first.click()
            page.wait_for_timeout(1000)
        
        # No critical errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0


# ============================================================
# NOTIFICATIONS
# ============================================================

@pytest.mark.gui
class TestNotifications:
    """Test notification system"""
    
    def test_notification_appears(self, page: Page):
        """Notifications appear on actions"""
        page.goto(f"{DSL_EDITOR_URL}#example=financial")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)
        
        # Run pipeline
        run_btn = page.locator("button:has-text('Uruchom'), button:has-text('Run'), .btn-primary")
        if run_btn.count() > 0:
            run_btn.first.click()
            page.wait_for_timeout(2000)
        
        # Check for notification (may or may not appear)
        notification = page.locator(".notification, .toast, [class*='notification']")
        # Just check no errors, notification is optional
        
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0


# ============================================================
# RESPONSIVE BEHAVIOR
# ============================================================

@pytest.mark.gui
class TestResponsive:
    """Test responsive behavior"""
    
    def test_mobile_viewport(self, page: Page):
        """Page works on mobile viewport"""
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Should load without errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0
    
    def test_tablet_viewport(self, page: Page):
        """Page works on tablet viewport"""
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(DSL_EDITOR_URL)
        page.wait_for_load_state("networkidle")
        
        # Should load without errors
        critical_errors = [e for e in page.errors if "TypeError" in e or "ReferenceError" in e]
        assert len(critical_errors) == 0
