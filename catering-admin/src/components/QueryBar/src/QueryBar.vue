<script setup lang="ts">
import { computed, ref } from 'vue'
import { Search } from '@/components/Search'
import { FormSchema } from '@/components/Form'

defineOptions({
  name: 'QueryBar'
})

/** 查询条件宽度单位（px） */
const SEARCH_CONDITION_UNIT = 160

/** 查询条件配置 */
export interface QueryCondition {
  field: string // 字段名
  label: string // 标签文字（不显示，仅用于占位符等）
  type: 'select' | 'input' | 'number' // 条件类型：下拉框、字符输入框、数字输入框
  options?: Array<{ label: string; value: any }> | (() => Array<{ label: string; value: any }>) // 下拉框选项（仅 type='select' 时使用）
  placeholder?: string // 占位符
  units?: number // 宽度单位（160px为单位），默认 1。模糊查询默认 3
  [key: string]: any // 其他属性
}

interface Props {
  conditions?: QueryCondition[] // 查询条件配置
}

const props = withDefaults(defineProps<Props>(), {
  conditions: () => []
})

const emit = defineEmits<{
  search: [data: Record<string, any>]
  reset: []
}>()

/** Search 组件引用 */
const searchRef = ref<InstanceType<typeof Search>>()

/**
 * 将查询条件配置转换为 FormSchema
 */
const searchSchema = computed<FormSchema[]>(() => {
  if (!props.conditions || props.conditions.length === 0) {
    return []
  }

  // 查找模糊查询字段（第一个 input 类型）
  const fuzzyQueryIndex = props.conditions.findIndex(c => c.type === 'input')

  return props.conditions.map((condition, index) => {
    // 计算宽度：模糊查询固定3单位（480px），其他根据 units 配置
    const isFuzzyQuery = condition.type === 'input' && index === fuzzyQueryIndex
    const units = isFuzzyQuery ? 3 : (condition.units ?? 1)
    const width = `${units * SEARCH_CONDITION_UNIT}px`

    const baseSchema: FormSchema = {
      field: condition.field,
      label: '', // 不显示 label
      formItemProps: {
        labelWidth: '0px' // 设置 label 宽度为 0
      },
      componentProps: {
        clearable: true,
        style: {
          width
        },
        placeholder: condition.placeholder || `请输入${condition.label}`
      } as any
    }

    switch (condition.type) {
      case 'select':
        baseSchema.component = 'Select'
        const options = typeof condition.options === 'function' 
          ? condition.options() 
          : condition.options || []
        baseSchema.componentProps = {
          ...baseSchema.componentProps,
          options
        }
        break

      case 'number':
        baseSchema.component = 'InputNumber'
        baseSchema.componentProps = {
          ...baseSchema.componentProps,
          ...condition,
          style: {
            ...baseSchema.componentProps.style
          }
        }
        break

      case 'input':
      default:
        baseSchema.component = 'Input'
        // 模糊查询框添加特殊属性用于 CSS 选择
        if (index === fuzzyQueryIndex) {
          baseSchema.componentProps = {
            ...baseSchema.componentProps,
            'data-fuzzy-query': true // 添加 data 属性用于 CSS 选择
          } as any
        }
        break
    }

    return baseSchema
  })
})

/**
 * 处理查询
 */
const handleSearch = (data: any) => {
  emit('search', data)
}

/**
 * 处理重置
 */
const handleReset = () => {
  emit('reset')
}

defineExpose({
  searchRef
})
</script>

<template>
  <div v-if="searchSchema.length > 0" class="query-bar">
    <Search 
      ref="searchRef" 
      :schema="searchSchema" 
      :label-width="0"
      :button-position="'left'"
      :show-reset="true"
      @search="handleSearch"
      @reset="handleReset"
    />
  </div>
</template>

<style scoped>
/* 查询条件区域 */
.query-bar {
  margin-bottom: 10px;
}

/* 查询条件样式优化 */
.query-bar :deep(.el-form) {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: flex-start !important; /* 强制左对齐 */
  gap: 0;
}

.query-bar :deep(.el-form--inline) {
  display: flex !important;
  justify-content: flex-start !important; /* 强制左对齐 */
}

.query-bar :deep(.el-form-item) {
  margin-right: 10px; /* 查询条件之间间距 10px */
  margin-bottom: 0;
  margin-left: 0 !important; /* 确保没有左外边距导致右移 */
  flex-shrink: 0;
  float: none !important; /* 确保不使用 float */
  width: fit-content; /* 根据内容自适应宽度 */
  text-align: left; /* 确保组件本身左对齐 */
}

.query-bar :deep(.el-form-item__content) {
  width: 100%; /* 占据 form-item 的全部宽度 */
}

.query-bar :deep(.el-form-item__label) {
  display: none !important; /* 隐藏 label */
  width: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* 查询按钮与查询条件之间的间距 */
.query-bar :deep(.el-form-item:last-child) {
  margin-left: 10px; /* 查询按钮与查询条件之间间距 10px */
  margin-right: 0; /* 确保按钮区域不右对齐 */
  flex-shrink: 0;
}

/* 确保按钮区域内的按钮左对齐 */
.query-bar :deep(.el-form-item:last-child .el-form-item__content) {
  display: flex;
  justify-content: flex-start; /* 按钮左对齐 */
  gap: 10px;
}

/* 覆盖 Element Plus 默认的最小宽度限制，使用我们定义的160px单位宽度 */
.query-bar :deep(.el-form-item__content > :first-child) {
  min-width: auto !important; /* 移除默认的 229.5px 最小宽度限制 */
}

.query-bar :deep(.el-input-number) {
  min-width: auto !important; /* 移除默认的 229.5px 最小宽度限制 */
}

/* 模糊查询框：固定宽度，确保宽度与占宽一致 */
.query-bar :deep(.el-form-item:has([data-fuzzy-query])) {
  width: 480px !important; /* 固定3单位宽度（160px * 3） */
  flex: none; /* 不使用 flex，避免宽度不一致 */
}

.query-bar :deep(.el-form-item:has([data-fuzzy-query]) .el-form-item__content) {
  width: 100% !important; /* 确保 content 占据全部宽度 */
}

.query-bar :deep(.el-form-item:has([data-fuzzy-query]) .el-input) {
  width: 100% !important; /* 确保输入框宽度与父容器一致 */
}

/* 数字输入框：确保组件左对齐，只有输入框内文字右对齐 */
.query-bar :deep(.el-input-number) {
  width: 100%;
}

.query-bar :deep(.el-input-number .el-input__inner) {
  text-align: right; /* 只影响输入框内的文字 */
}
</style>

