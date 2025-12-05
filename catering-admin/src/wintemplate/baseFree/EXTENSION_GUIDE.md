# BaseFree 模板扩展指南

## 概述

`BaseFree.vue` 是一个通用表单模板，提供了 6 个扩展点，允许在不修改模板代码的情况下满足个性化需求。

## 扩展点说明

### 扩展点1：字段级别的自定义转换 (`customConvert`)

**用途**：为特定字段提供完全自定义的渲染逻辑

**使用场景**：
- 某个字段需要特殊的组件或交互
- 字段的显示逻辑与模板默认处理不同

**示例**：

```typescript
// Response.vue
export const formSchema: FreeFormField[] = [
  {
    field: 'special_field',
    label: '特殊字段',
    component: 'Input',
    // 字段级别的自定义转换
    customConvert: (field, data, mode) => {
      // 返回自定义的 FormSchema
      return {
        ...field,
        formItemProps: {
          slots: {
            default: (formData: any) => {
              // 完全自定义的渲染逻辑
              return (
                <div>
                  <CustomComponent 
                    value={formData.special_field}
                    onChange={(val) => formData.special_field = val}
                  />
                </div>
              )
            }
          }
        }
      }
    }
  }
]
```

---

### 扩展点2：全局字段转换函数 (`customFieldConvert`)

**用途**：为所有字段提供统一的转换逻辑

**使用场景**：
- 需要统一处理某些类型的字段
- 批量修改字段行为

**示例**：

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="formSchema"
    :custom-field-convert="handleFieldConvert"
    ...
  />
</template>

<script setup lang="tsx">
const handleFieldConvert = (field: FreeFormField, data: any) => {
  // 如果字段名包含 'special'，使用自定义处理
  if (field.field.includes('special')) {
    return {
      ...field,
      componentProps: {
        ...field.componentProps,
        customProp: true
      }
    }
  }
  // 返回 null 表示使用模板默认处理
  return null
}
</script>
```

---

### 扩展点3：提交前的数据处理钩子 (`beforeSubmit`)

**用途**：在表单提交前对数据进行处理或验证

**使用场景**：
- 需要转换数据格式
- 需要添加额外的数据字段
- 需要执行额外的验证

**示例**：

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="formSchema"
    :before-submit="handleBeforeSubmit"
    ...
  />
</template>

<script setup lang="tsx">
const handleBeforeSubmit = async (formData: any) => {
  // 转换数据格式
  const processedData = {
    ...formData,
    // 添加额外字段
    extra_field: 'value',
    // 转换日期格式
    date_field: formatDate(formData.date_field)
  }
  
  // 可以抛出错误来阻止提交
  if (!processedData.required_field) {
    throw new Error('缺少必填字段')
  }
  
  return processedData
}
</script>
```

---

### 扩展点4：初始化后的钩子 (`afterInit`)

**用途**：在表单数据初始化完成后执行操作

**使用场景**：
- 需要根据初始化数据执行额外操作
- 需要设置额外的状态

**示例**：

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="formSchema"
    :after-init="handleAfterInit"
    ...
  />
</template>

<script setup lang="tsx">
const handleAfterInit = (formData: any) => {
  // 根据初始化数据执行操作
  if (formData.status === 'active') {
    // 执行某些操作
    console.log('数据已激活')
  }
}
</script>
```

---

### 扩展点5：Tab 级别的自定义内容 (`customContent` + 插槽)

**用途**：为特定 Tab 提供完全自定义的内容

**使用场景**：
- Tab 内容不是表单，而是其他组件
- 需要复杂的自定义布局

**示例**：

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="formSchema"
    :tabs="tabs"
    ...
  >
    <!-- 自定义 Tab 内容 -->
    <template #tab-custom="{ tab, currentRow, mode }">
      <div>
        <h3>自定义内容</h3>
        <CustomComponent :data="currentRow" />
      </div>
    </template>
    
    <!-- 自定义操作日志 Tab -->
    <template #tab-log="{ tab, currentRow, mode }">
      <OperationLog :record-id="currentRow?.id" />
    </template>
  </BaseFree>
</template>

<script setup lang="tsx">
const tabs = [
  { label: '基础信息', name: 'basic' },
  { 
    label: '自定义内容', 
    name: 'custom',
    customContent: true // 启用自定义内容
  },
  { 
    label: '操作日志', 
    name: 'log',
    customContent: true // 启用自定义内容
  }
]
</script>
```

---

### 扩展点6：按钮区域自定义 (`buttons` 插槽)

**用途**：完全自定义按钮区域

**使用场景**：
- 需要额外的按钮
- 需要自定义按钮布局
- 需要自定义按钮样式

**示例**：

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="formSchema"
    ...
  >
    <!-- 自定义按钮区域 -->
    <template #buttons="{ save, cancel, mode, saveLoading }">
      <div class="custom-buttons">
        <PrompInfo ref="prompInfoRef" />
        <ElButton @click="handlePreview">预览</ElButton>
        <ElButton 
          v-if="mode !== 'view'"
          type="primary" 
          :loading="saveLoading"
          @click="save"
        >
          保存
        </ElButton>
        <ElButton @click="cancel">返回</ElButton>
      </div>
    </template>
  </BaseFree>
</template>
```

---

## 组合使用示例

### 场景1：复杂字段 + 自定义 Tab

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="formSchema"
    :tabs="tabs"
    :before-submit="handleBeforeSubmit"
    ...
  >
    <!-- 自定义 Tab 内容 -->
    <template #tab-charts="{ tab, currentRow, mode }">
      <ChartsComponent :data="currentRow" />
    </template>
  </BaseFree>
</template>

<script setup lang="tsx">
// 字段配置中包含自定义转换
export const formSchema: FreeFormField[] = [
  {
    field: 'complex_field',
    label: '复杂字段',
    customConvert: (field, data, mode) => {
      // 自定义转换逻辑
      return { ...field, /* ... */ }
    }
  }
]

const tabs = [
  { label: '基础信息', name: 'basic' },
  { label: '图表', name: 'charts', customContent: true }
]

const handleBeforeSubmit = async (data) => {
  // 数据处理
  return processedData
}
</script>
```

### 场景2：完全自定义的页面

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    :form-schema="[]"
    :tabs="tabs"
    ...
  >
    <!-- 完全自定义按钮 -->
    <template #buttons="{ save, cancel }">
      <CustomButtonBar @save="save" @cancel="cancel" />
    </template>
    
    <!-- 完全自定义 Tab 内容 -->
    <template #tab-main="{ currentRow, mode }">
      <CustomForm :data="currentRow" :mode="mode" />
    </template>
  </BaseFree>
</template>

<script setup lang="tsx">
const tabs = [
  { label: '主要内容', name: 'main', customContent: true }
]
</script>
```

---

## 最佳实践

### 1. 优先级原则

扩展点的优先级（从高到低）：
1. **字段级别的 `customConvert`** - 最高优先级
2. **全局的 `customFieldConvert`** - 中等优先级
3. **模板默认处理** - 最低优先级

### 2. 使用建议

- **标准需求**：使用模板默认处理，只配置 `formSchema`
- **简单个性化**：使用 `beforeSubmit` 或 `afterInit` 钩子
- **字段个性化**：使用字段级别的 `customConvert`
- **Tab 个性化**：使用 `customContent: true` + 插槽
- **完全自定义**：使用 `buttons` 插槽 + `customContent` 插槽

### 3. 性能考虑

- `customConvert` 和 `customFieldConvert` 会在每次字段转换时调用，避免复杂计算
- `beforeSubmit` 和 `afterInit` 只在特定时机调用，可以执行较复杂的操作

### 4. 代码组织

- 将扩展逻辑放在使用方的组件中，而不是模板中
- 使用 TypeScript 类型定义，确保类型安全
- 为复杂的扩展逻辑添加注释说明

---

## 总结

通过这 6 个扩展点，`BaseFree` 模板可以满足：
- ✅ 大部分标准需求（使用默认处理）
- ✅ 简单的个性化需求（使用钩子函数）
- ✅ 复杂的个性化需求（使用插槽和自定义转换）
- ✅ 完全自定义的需求（使用所有扩展点）

**核心原则**：模板保持简洁，个性化需求通过扩展点实现，不增加模板的学习成本。

