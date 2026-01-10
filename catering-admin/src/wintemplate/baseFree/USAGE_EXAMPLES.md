# BaseFree 扩展使用示例

## 示例1：标准使用（无扩展）

这是最常见的使用方式，适用于大部分标准需求：

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    v-model="dialogVisible"
    :title="dialogTitle"
    :mode="dialogMode"
    :form-schema="formSchema"
    :rules="rules"
    :current-row="currentRow"
    :submit-api="submitApi"
    :tabs="tabs"
    :save-loading="saveLoading"
    @success="handleSuccess"
    @cancel="handleCancel"
  />
</template>

<script setup lang="tsx">
import { formSchema, rules, tabs } from './components/Response.vue'
// ... 其他代码
</script>
```

---

## 示例2：使用提交前钩子（数据转换）

**需求**：提交前需要转换数据格式或添加额外字段

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    v-model="dialogVisible"
    :form-schema="formSchema"
    :before-submit="handleBeforeSubmit"
    ...
  />
</template>

<script setup lang="tsx">
const handleBeforeSubmit = async (formData: any) => {
  // 转换数据格式
  return {
    ...formData,
    // 添加时间戳
    timestamp: Date.now(),
    // 转换日期格式
    created_date: formatDate(formData.created_date),
    // 处理图片字段（如果需要特殊处理）
    images: formData.dish_images?.map((img: any) => {
      if (Array.isArray(img)) return img[0]
      return img
    })
  }
}
</script>
```

---

## 示例3：字段级别的自定义转换

**需求**：某个字段需要特殊的组件或交互逻辑

```vue
<!-- Test.vue -->
<script setup lang="tsx">
import { FreeFormField } from '@/wintemplate/BaseFree'

const formSchema: FreeFormField[] = [
  {
    field: 'name',
    label: '名称',
    component: 'Input'
  },
  {
    field: 'special_field',
    label: '特殊字段',
    component: 'Input',
    // 字段级别的自定义转换
    customConvert: (field, data, mode) => {
      return {
        ...field,
        formItemProps: {
          slots: {
            default: (formData: any) => {
              return (
                <div>
                  <ElInput
                    v-model={formData.special_field}
                    placeholder="请输入特殊字段"
                    disabled={mode === 'view'}
                  />
                  <ElButton 
                    size="small" 
                    onClick={() => {
                      // 特殊操作
                      formData.special_field = '特殊值'
                    }}
                  >
                    自动填充
                  </ElButton>
                </div>
              )
            }
          }
        }
      }
    }
  }
]
</script>
```

---

## 示例4：自定义 Tab 内容

**需求**：某个 Tab 不是表单，而是其他内容（如操作日志、图表等）

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    v-model="dialogVisible"
    :form-schema="formSchema"
    :tabs="tabs"
    ...
  >
    <!-- 自定义操作日志 Tab -->
    <template #tab-log="{ tab, currentRow, mode }">
      <OperationLog 
        v-if="currentRow?.id"
        :record-id="currentRow.id"
        :mode="mode"
      />
    </template>
    
    <!-- 自定义统计 Tab -->
    <template #tab-statistics="{ tab, currentRow, mode }">
      <StatisticsPanel :data="currentRow" />
    </template>
  </BaseFree>
</template>

<script setup lang="tsx">
import { FreeTab } from '@/wintemplate/BaseFree'

const tabs: FreeTab[] = [
  { label: '基础信息', name: 'basic' },
  { 
    label: '操作日志', 
    name: 'log',
    customContent: true // 启用自定义内容
  },
  { 
    label: '统计信息', 
    name: 'statistics',
    customContent: true // 启用自定义内容
  }
]
</script>
```

---

## 示例5：自定义按钮区域

**需求**：需要额外的按钮或自定义按钮布局

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    v-model="dialogVisible"
    :form-schema="formSchema"
    ...
  >
    <!-- 自定义按钮区域 -->
    <template #buttons="{ save, cancel, mode, saveLoading }">
      <div class="custom-buttons-wrapper">
        <div class="buttons-left">
          <PrompInfo ref="prompInfoRef" />
        </div>
        <div class="buttons-right">
          <!-- 额外的预览按钮 -->
          <ElButton 
            v-if="mode !== 'view'"
            @click="handlePreview"
          >
            预览
          </ElButton>
          <!-- 额外的复制按钮 -->
          <ElButton 
            v-if="mode === 'edit'"
            @click="handleCopy"
          >
            复制
          </ElButton>
          <!-- 保存按钮 -->
          <ButtonPlus
            v-if="mode !== 'view'"
            stype="save"
            :loading="saveLoading"
            @click="save"
          />
          <!-- 返回按钮 -->
          <ButtonPlus
            stype="return"
            @click="cancel"
          />
        </div>
      </div>
    </template>
  </BaseFree>
</template>

<script setup lang="tsx">
const handlePreview = () => {
  // 预览逻辑
}

const handleCopy = () => {
  // 复制逻辑
}
</script>

<style scoped lang="less">
.custom-buttons-wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  margin-bottom: 15px;
}

.buttons-left {
  flex: 1;
}

.buttons-right {
  display: flex;
  gap: 10px;
}
</style>
```

---

## 示例6：组合使用多个扩展点

**需求**：一个页面需要多个个性化功能

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    v-model="dialogVisible"
    :title="dialogTitle"
    :mode="dialogMode"
    :form-schema="formSchema"
    :rules="rules"
    :current-row="currentRow"
    :submit-api="submitApi"
    :tabs="tabs"
    :before-submit="handleBeforeSubmit"
    :after-init="handleAfterInit"
    :custom-field-convert="handleFieldConvert"
    :save-loading="saveLoading"
    @success="handleSuccess"
    @cancel="handleCancel"
  >
    <!-- 自定义操作日志 Tab -->
    <template #tab-log="{ currentRow }">
      <OperationLog :record-id="currentRow?.id" />
    </template>
    
    <!-- 自定义按钮区域 -->
    <template #buttons="{ save, cancel, mode }">
      <div class="custom-buttons">
        <PrompInfo ref="prompInfoRef" />
        <ElButton v-if="mode === 'edit'" @click="handleCopy">复制</ElButton>
        <ButtonPlus v-if="mode !== 'view'" stype="save" @click="save" />
        <ButtonPlus stype="return" @click="cancel" />
      </div>
    </template>
  </BaseFree>
</template>

<script setup lang="tsx">
import { FreeFormField, FreeTab } from '@/wintemplate/BaseFree'

// 字段配置（包含字段级别的自定义转换）
const formSchema: FreeFormField[] = [
  {
    field: 'name',
    label: '名称',
    component: 'Input'
  },
  {
    field: 'special_field',
    label: '特殊字段',
    component: 'Input',
    customConvert: (field, data, mode) => {
      // 字段级别的自定义处理
      return {
        ...field,
        formItemProps: {
          slots: {
            default: (formData: any) => {
              return <CustomSpecialField v-model={formData.special_field} />
            }
          }
        }
      }
    }
  }
]

// Tab 配置（包含自定义 Tab）
const tabs: FreeTab[] = [
  { label: '基础信息', name: 'basic' },
  { label: '操作日志', name: 'log', customContent: true }
]

// 全局字段转换函数
const handleFieldConvert = (field: FreeFormField, data: any) => {
  // 统一处理某些类型的字段
  if (field.field.includes('price')) {
    return {
      ...field,
      componentProps: {
        ...field.componentProps,
        prefix: '¥'
      }
    }
  }
  return null // 使用模板默认处理
}

// 提交前钩子
const handleBeforeSubmit = async (formData: any) => {
  // 数据转换
  return {
    ...formData,
    processed_at: new Date().toISOString()
  }
}

// 初始化后钩子
const handleAfterInit = (formData: any) => {
  // 根据初始化数据执行操作
  if (formData.status === 'active') {
    console.log('数据已激活')
  }
}
</script>
```

---

## 示例7：完全自定义的页面

**需求**：整个页面都需要自定义，但想利用 BaseFree 的抽屉和基础结构

```vue
<!-- Test.vue -->
<template>
  <BaseFree
    v-model="dialogVisible"
    :title="dialogTitle"
    :mode="dialogMode"
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
      <CustomForm 
        :data="currentRow" 
        :mode="mode"
        @submit="save"
      />
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

## 总结

通过这些示例，可以看到：

1. **标准需求**：只需配置 `formSchema`、`rules`、`tabs` 等基本属性
2. **简单个性化**：使用 `beforeSubmit`、`afterInit` 等钩子函数
3. **字段个性化**：在 `formSchema` 中使用 `customConvert`
4. **Tab 个性化**：使用 `customContent: true` + 插槽
5. **按钮个性化**：使用 `buttons` 插槽
6. **完全自定义**：组合使用所有扩展点

**关键点**：
- 模板保持简洁，不增加学习成本
- 个性化需求通过扩展点实现，不修改模板代码
- 扩展点可以组合使用，满足复杂需求

