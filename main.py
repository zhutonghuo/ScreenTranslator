import os
import sys
import time
import traceback

LOG_DIR = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "ScreenTranslator")
LOG_FILE = os.path.join(LOG_DIR, "crash.log")


def write_crash(title, detail):
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n=== {time.strftime('%Y-%m-%d %H:%M:%S')} {title} ===\n{detail}\n")
    except Exception:
        pass


os.environ.setdefault("ARGOS_CHUNK_TYPE", "MINISBD")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QIcon
    from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

    from core.controller import Controller, app_icon_path
    from core.settings import DEFAULT_HOTKEYS, HK_LABELS, HOTKEY_ITEMS, Settings
    from ui.hotkey import HotkeyManager
    from ui.main_window import MainWindow
except Exception:
    write_crash("import-failed", traceback.format_exc())
    raise

HK = {name: i + 1 for i, (name, _, _) in enumerate(HOTKEY_ITEMS)}


def hk_display(settings, name):
    cfg = (settings.get("hotkeys") or {}).get(name, {})
    if cfg.get("enabled", True) and cfg.get("key"):
        return cfg["key"]
    return "未设置"


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    icon_path = app_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    settings = Settings()
    ctrl = Controller(settings)
    ctrl.translator.custom_token = settings.get("caiyun_token", "")
    win = MainWindow(settings, ctrl)
    ctrl.bind(status=win.on_status, result=win.on_result, region=win.on_region, state=win.on_state)
    region = settings.get_region()
    if region:
        win.on_region(region)
    win.show()

    def _toggle_main():
        if win.isVisible() and not win.isMinimized():
            win.hide()
        else:
            win.show()
            win.raise_()
            win.activateWindow()

    def _on_hotkey(logical_id):
        action = {
            HK["capture_once"]: ctrl.capture_once,
            HK["toggle_monitor"]: ctrl.toggle_monitor,
            HK["toggle_main"]: _toggle_main,
        }.get(logical_id)
        if action:
            action()

    host = QWidget()
    hk = HotkeyManager(host, _on_hotkey)
    app.installNativeEventFilter(hk)

    def build_mappings():
        hk_cfg = settings.get("hotkeys") or {}
        maps = []
        for name, lid in HK.items():
            cfg = hk_cfg.get(name) or {}
            maps.append((lid, cfg.get("key", ""), cfg.get("enabled", True)))
        return maps

    def reload_hotkeys():
        failed = hk.register_all(build_mappings())
        refresh_tray_labels()
        if failed:
            names = "、".join(HK_LABELS.get(f, str(f)) for f in failed)
            win.on_status("以下快捷键注册失败（可能被占用或组合无效）：" + names)
        else:
            win.on_status("快捷键已应用")

    def suspend_hotkeys():
        hk.unregister_all()

    failed = hk.register_all(build_mappings())
    if failed:
        names = "、".join(HK_LABELS.get(f, str(f)) for f in failed)
        win.on_status("部分快捷键未生效（可能被占用或组合无效）：" + names)
    else:
        win.on_status("全局快捷键已就绪")

    ctrl.bind(hotkeys=reload_hotkeys, hotkeys_suspend=suspend_hotkeys)

    tray = QSystemTrayIcon(QIcon(icon_path) if icon_path else QIcon(), app)
    tray.setToolTip("屏幕实时翻译")
    menu = QMenu()
    act_main = menu.addAction("显示 / 隐藏主界面")
    act_once = menu.addAction("单次截图翻译")
    act_toggle = menu.addAction("开始 / 停止监控")
    act_pick = menu.addAction("框选监控区域")
    menu.addSeparator()
    act_overlay = menu.addAction("显示悬浮窗")
    menu.addSeparator()
    act_quit = menu.addAction("退出")
    act_main.triggered.connect(_toggle_main)
    act_once.triggered.connect(ctrl.capture_once)
    act_toggle.triggered.connect(ctrl.toggle_monitor)
    act_pick.triggered.connect(ctrl.pick_region)
    act_overlay.triggered.connect(ctrl.overlay.show)
    act_quit.triggered.connect(app.quit)
    tray.setContextMenu(menu)
    tray.activated.connect(
        lambda reason: _toggle_main()
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick)
        else None
    )
    tray_actions = {"main": act_main, "once": act_once, "toggle": act_toggle}

    def refresh_tray_labels():
        tray_actions["main"].setText("显示 / 隐藏主界面 (" + hk_display(settings, "toggle_main") + ")")
        tray_actions["once"].setText("单次截图翻译 (" + hk_display(settings, "capture_once") + ")")
        tray_actions["toggle"].setText("开始 / 停止监控 (" + hk_display(settings, "toggle_monitor") + ")")

    refresh_tray_labels()
    tray.show()

    if settings.get("auto_start") and settings.get_region():
        ctrl.start_monitor()

    app.aboutToQuit.connect(ctrl.shutdown)
    sys.exit(app.exec())


if __name__ == "__main__":
    def _hook(exc_type, exc_value, exc_tb):
        write_crash("uncaught", "".join(traceback.format_exception(exc_type, exc_value, exc_tb)))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        write_crash("startup", traceback.format_exc())
        try:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.critical(None, "启动失败", traceback.format_exc()[-1500:])
        except Exception:
            pass
        sys.exit(1)
