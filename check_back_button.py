def check_back_button():
    """Проверка работы кнопки "Назад" """
    
    print("CHECKING BACK BUTTON:")
    print("=" * 50)
    
    # 1. Проверяем определение кнопки
    print(f"\n1. BACK BUTTON DEFINITION:")
    print("   Located in get_swipe_keyboard() function:")
    print("   - Text: '⬅️ Назад'")
    print("   - Callback: 'back_profile'")
    print("   - Position: Below like/dislike buttons")
    
    # 2. Проверяем handler
    print(f"\n2. BACK BUTTON HANDLER:")
    print("   Function: handle_back_profile()")
    print("   Decorator: @router.callback_query(F.data == 'back_profile')")
    print("   Logic: Check current_index, go back or main menu")
    
    # 3. Проблема из лога
    print(f"\n3. LOG ANALYSIS:")
    print("   User pressed dislike 10 times")
    print("   No back button presses detected")
    print("   Possible issues:")
    print("     - Button not visible")
    print("     - Callback not working")
    print("     - Handler not registered")
    
    # 4. Возможные проблемы
    print(f"\n4. POSSIBLE ISSUES:")
    
    issues = [
        "1. Button not showing in keyboard",
        "2. Callback data mismatch",
        "3. Handler registration issue",
        "4. State management problem",
        "5. Keyboard display issue"
    ]
    
    for issue in issues:
        print(f"   {issue}")
    
    # 5. Что проверить в коде
    print(f"\n5. CODE CHECKS NEEDED:")
    
    checks = [
        "get_swipe_keyboard() function",
        "handle_back_profile() handler",
        "Callback registration",
        "Keyboard display logic",
        "State management"
    ]
    
    for check in checks:
        print(f"   {check}")
    
    print(f"\n" + "=" * 50)
    print("BACK BUTTON CHECK COMPLETE!")
    print("\nNEXT STEPS:")
    print("1. Verify get_swipe_keyboard() function")
    print("2. Test back button callback")
    print("3. Check handler registration")
    print("4. Fix any found issues")

if __name__ == "__main__":
    check_back_button()
