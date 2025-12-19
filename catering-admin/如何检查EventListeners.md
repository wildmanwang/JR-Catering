# 如何检查 Event Listeners

## 方法一：使用 Chrome DevTools 检查 Event Listeners

1. **打开开发者工具**
   - 按 `F12` 或 `Ctrl+Shift+I` (Windows/Linux)
   - 或 `Cmd+Option+I` (Mac)

2. **选择 Elements 标签页**
   - 点击左上角的 Elements 标签（或按 `Ctrl+Shift+C` 选择元素）

3. **选择要检查的元素**
   - 在编辑模式下，点击表格中的输入框（如 ElInputNumber、ElInput、ElSelect）
   - 或者使用选择工具（左上角的箭头图标）点击输入框

4. **查看 Event Listeners**
   - 在右侧面板中找到 "Event Listeners" 标签页
   - 展开 `keydown` 事件
   - 你应该能看到绑定的事件监听器列表

5. **检查监听器详情**
   - 点击监听器可以查看：
     - 监听器的位置（哪个文件、哪一行）
     - 是否使用了捕获阶段（capture: true）
     - 监听器的函数代码

## 方法二：使用 Console 检查

在浏览器控制台中运行以下代码：

```javascript
// 检查当前焦点元素的事件监听器
const activeElement = document.activeElement;
console.log('Active Element:', activeElement);

// 检查是否有 keydown 事件监听器
const listeners = getEventListeners(activeElement);
console.log('Event Listeners:', listeners);

// 检查 keydown 事件
if (listeners && listeners.keydown) {
  console.log('Keydown Listeners:', listeners.keydown);
  listeners.keydown.forEach((listener, index) => {
    console.log(`Listener ${index}:`, {
      listener: listener.listener,
      useCapture: listener.useCapture,
      passive: listener.passive,
      once: listener.once
    });
  });
}
```

## 方法三：手动测试事件是否被触发

在浏览器控制台中运行以下代码来测试 Tab 键是否被捕获：

```javascript
// 添加一个测试监听器
const testListener = (e) => {
  if (e.key === 'Tab' || e.keyCode === 9) {
    console.log('Tab key detected!', {
      key: e.key,
      keyCode: e.keyCode,
      code: e.code,
      target: e.target,
      currentTarget: e.currentTarget,
      defaultPrevented: e.defaultPrevented
    });
  }
};

// 在捕获阶段监听
window.addEventListener('keydown', testListener, true);
document.addEventListener('keydown', testListener, true);

// 在编辑模式下按 Tab 键，查看控制台输出
// 如果看到输出，说明事件被触发了
// 如果没有输出，说明事件可能被更早地拦截了
```

## 方法四：检查是否有其他监听器拦截了 Tab 键

```javascript
// 检查所有可能拦截 Tab 键的监听器
const checkTabInterceptors = () => {
  // 检查 window 级别
  const windowListeners = getEventListeners(window);
  console.log('Window Listeners:', windowListeners);
  
  // 检查 document 级别
  const documentListeners = getEventListeners(document);
  console.log('Document Listeners:', documentListeners);
  
  // 检查当前焦点元素
  const activeElement = document.activeElement;
  if (activeElement) {
    const elementListeners = getEventListeners(activeElement);
    console.log('Active Element Listeners:', elementListeners);
    
    // 检查父元素
    let parent = activeElement.parentElement;
    let level = 0;
    while (parent && level < 5) {
      const parentListeners = getEventListeners(parent);
      if (parentListeners && parentListeners.keydown) {
        console.log(`Parent Level ${level} Listeners:`, parentListeners);
      }
      parent = parent.parentElement;
      level++;
    }
  }
};

checkTabInterceptors();
```

## 方法五：使用 Performance Monitor

1. **打开 Performance Monitor**
   - 在 Chrome DevTools 中，按 `Ctrl+Shift+P` (Windows/Linux) 或 `Cmd+Shift+P` (Mac)
   - 输入 "Show Performance Monitor"
   - 选择 "Show Performance Monitor"

2. **监控事件**
   - 在编辑模式下按 Tab 键
   - 查看 Performance Monitor 中的事件计数
   - 如果事件计数增加，说明事件被触发了

## 常见问题排查

### 1. 如果看不到 Event Listeners 标签页
- 确保选择了正确的元素（输入框元素，而不是外层容器）
- 尝试刷新页面后重新检查

### 2. 如果看到监听器但没有响应
- 检查监听器是否使用了 `capture: true`（应该在捕获阶段）
- 检查是否有其他监听器在更早的阶段拦截了事件
- 检查监听器的 `passive` 属性（应该是 `false`，才能阻止默认行为）

### 3. 如果事件根本没有被触发
- 检查是否有其他全局监听器拦截了 Tab 键
- 检查 Element Plus 组件是否有特殊处理
- 尝试使用 `keyup` 事件而不是 `keydown`

## 调试技巧

1. **添加临时日志**
   ```javascript
   // 在 handleGlobalKeydown 函数开头添加
   console.log('handleGlobalKeydown called', event.key, editingCell.value);
   ```

2. **检查事件传播**
   ```javascript
   // 在事件监听器中添加
   console.log('Event phase:', event.eventPhase); // 1=捕获, 2=目标, 3=冒泡
   console.log('Event target:', event.target);
   console.log('Event currentTarget:', event.currentTarget);
   ```

3. **检查默认行为是否被阻止**
   ```javascript
   // 在事件监听器中添加
   console.log('Default prevented:', event.defaultPrevented);
   console.log('Propagation stopped:', event.cancelBubble);
   ```

