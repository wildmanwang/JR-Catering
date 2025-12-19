<script setup lang="tsx">
import { computed, watch, toRefs } from 'vue'
import { ElUpload, UploadProps, ElIcon, ElImage, ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useAuthStore } from '@/store/modules/auth'
import {
  processImageList,
  removeSortPrefix,
  removeQueryParams
} from '@/utils/imageList'

// ==================== Props 定义 ====================
interface Props {
  /** 图片数据（字符串或数组，如果是数组则自动取第一张） */
  modelValue?: string | string[] | null
  /** 是否禁用（查看模式） */
  disabled?: boolean
  /** 图片尺寸：normal（100px*100px，默认）或 small（60px*60px） */
  size?: 'normal' | 'small'
  /** 默认图片路径（无图时显示，默认：/src/assets/imgs/no_image.png） */
  defaultImage?: string
  /** 上传接口地址 */
  action?: string
  /** 上传时的额外数据 */
  data?: Record<string, any>
  /** 上传时的请求头 */
  headers?: Record<string, string>
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  disabled: false,
  size: 'normal',
  defaultImage: '/src/assets/imgs/no_image.png',
  action: '/api/vadmin/system/upload/image/to/local',
  data: () => ({ path: 'system' }),
  headers: () => ({})
})

// ==================== Emits 定义 ====================
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// ==================== Store ====================
const authStore = useAuthStore()
const token = computed(() => authStore.getToken)

// 解构 props 以便在模板中直接使用（使用 toRefs 保持响应性）
const { disabled, action, data, size, defaultImage } = toRefs(props)

// ==================== 计算属性 ====================
/**
 * 提取图片路径
 * 处理格式：
 * 1. "数字-路径" 格式（如 "10-/media/system/image.png"）-> 提取路径部分
 * 2. "数字http://..." 格式（如 "1http://..."）-> 移除数字前缀
 */
const extractImagePath = (url: string): string => {
  if (!url) return url

  // 使用 removeSortPrefix 处理 "数字-路径" 格式
  let processedUrl = removeSortPrefix(url)

  // 处理 "数字http://..." 格式（如 "1http://..."）
  // 注意：这种格式 removeSortPrefix 可能无法处理，需要额外处理
  if (/^\d+(https?:\/\/)/.test(processedUrl)) {
    processedUrl = processedUrl.replace(/^\d+(?=https?:\/\/)/, '')
  }

  return processedUrl
}

/**
 * 预处理输入的图片数据
 * 处理数组和字符串，过滤无效值，统一返回字符串或 null
 */
const preprocessImageValue = (value: any): string | null => {
  if (!value) return null

  let processedValue: any = value

  // 如果是数组，过滤、排序并取第一个有效值
  if (Array.isArray(value)) {
    // 过滤掉空值、null、undefined、空字符串和非字符串类型
    let validValues = value
      .filter((item) => typeof item === 'string' && item.trim() !== '')
      .map((item) => String(item).trim())
    
    if (validValues.length === 0) {
      return null
    }
    
    // 如果是 "数字-路径" 格式，使用 processImageList 处理排序和前缀
    if (validValues.length > 0 && /^\d+-/.test(validValues[0])) {
      validValues = processImageList(validValues)
    }
    
    // 取第一个有效值
    processedValue = validValues[0]
  } else if (typeof value !== 'string') {
    // 非字符串、非数组类型，返回 null
    return null
  } else {
    // 字符串类型，去除首尾空格
    processedValue = value.trim()
    if (processedValue === '') {
      return null
    }
  }

  // 提取图片路径（处理 "数字-路径" 和 "数字http://..." 格式）
  processedValue = extractImagePath(processedValue)

  return processedValue || null
}

/**
 * 处理输入的图片数据
 * 1. 预处理数组和字符串（过滤无效值）
 * 2. 移除数字前缀（如 "1http://..." -> "http://..."）
 * 3. 移除查询参数（如 "path?original" -> "path"）
 */
const imageUrl = computed({
  get: () => {
    const processedValue = preprocessImageValue(props.modelValue)
    if (!processedValue) return null

    let url: string = processedValue

    // 移除查询参数
    url = removeQueryParams(url)

    return url || null
  },
  set: (val) => {
    emit('update:modelValue', val)
  }
})

/**
 * 当前显示的图片 URL（如果有图则使用，无图则使用默认图）
 */
const displayImageUrl = computed(() => {
  return imageUrl.value || defaultImage.value
})

/**
 * 是否有图片
 */
const hasImage = computed(() => {
  return !!imageUrl.value
})

/**
 * 预览列表（用于 ElImage 的 preview-src-list）
 * 如果传入的是数组，返回所有有效的图片 URL（移除查询参数）
 * 如果是字符串，返回单个 URL
 */
const previewList = computed(() => {
  if (!hasImage.value) {
    return []
  }

  const value = props.modelValue
  if (!value) return []

    // 如果是数组，返回所有有效的图片 URL
    if (Array.isArray(value)) {
      // 过滤并排序（如果是 "数字-路径" 格式）
      let validValues = value
        .filter((item) => typeof item === 'string' && item.trim() !== '')
        .map((item) => String(item).trim())
      
      // 使用 processImageList 处理排序和前缀
      if (validValues.length > 0 && /^\d+-/.test(validValues[0])) {
        validValues = processImageList(validValues)
      }
      
      // 提取路径并移除查询参数
      const validUrls = validValues
        .map((item) => {
          let url = extractImagePath(item)
          // 移除查询参数
          url = removeQueryParams(url)
          return url
        })
        .filter((url) => url && url !== '')
      
      return validUrls.length > 0 ? validUrls : (imageUrl.value ? [imageUrl.value] : [])
    }

  // 如果是字符串，返回单个 URL
  return imageUrl.value ? [imageUrl.value] : []
})

/**
 * 是否显示上传组件（编辑模式且无图）
 */
const showUploader = computed(() => {
  return !disabled.value && !hasImage.value
})

// ==================== 合并请求头 ====================
const uploadHeaders = computed(() => {
  return {
    Authorization: token.value,
    ...props.headers
  }
})

// ==================== 上传前验证 ====================
const beforeImageUpload: UploadProps['beforeUpload'] = (rawFile) => {
  const isImage = ['image/jpeg', 'image/gif', 'image/png'].includes(rawFile.type)
  const isLtSize = rawFile.size / 1024 / 1024 < 2
  if (!isImage) {
    ElMessage.error('上传图片必须是 JPG/GIF/PNG 格式!')
  }
  if (!isLtSize) {
    ElMessage.error('上传图片大小不能超过2MB!')
  }
  return isImage && isLtSize
}

// ==================== 文件变化处理 ====================
/**
 * 文件选择后，生成预览 URL（不上传，只预览）
 */
const handleFileChange: UploadProps['onChange'] = (file) => {
  if (file.raw) {
    // 生成预览 URL
    const previewUrl = URL.createObjectURL(file.raw)
    // 更新图片数据（直接使用预览 URL，不上传）
    imageUrl.value = previewUrl
  }
}

// ==================== 删除图片 ====================
const handleRemoveImage = () => {
  imageUrl.value = null
}

// ==================== 图片加载失败处理 ====================
const handleError = (e: Event) => {
  const img = e.target as HTMLImageElement
  if (img && img.src && img.src !== defaultImage.value) {
    // 图片加载失败时，如果当前不是默认图，则显示默认图
    img.src = defaultImage.value
  }
}

// ==================== 监听外部数据变化 ====================
watch(
  () => props.modelValue,
  () => {
    // imageUrl computed 会自动处理数据变化
    // 这里不需要额外逻辑
  }
)
</script>

<template>
  <div :class="['image-single-container', `image-single-container-${size}`]">
    <!-- 查看模式：有图 -->
    <div v-if="hasImage && disabled" :class="`image-single-group-${size}`">
      <ElImage
        :src="displayImageUrl"
        :class="`image-single-item-${size}`"
        @error="handleError"
        :zoom-rate="1.2"
        :preview-src-list="previewList"
        preview-teleported
        hide-on-click-modal
        :initial-index="0"
        fit="cover"
        style="width: 100%; height: 100%"
      />
    </div>

    <!-- 查看模式：无图（显示默认图，不可预览） -->
    <div v-else-if="!hasImage && disabled" :class="`image-single-group-${size}`">
      <ElImage
        :src="defaultImage"
        :class="`image-single-item-${size}`"
        @error="handleError"
        fit="cover"
        style="width: 100%; height: 100%"
      />
    </div>

    <!-- 编辑模式：有图（可删除） -->
    <div v-else-if="hasImage && !disabled" :class="`image-single-group-${size}`">
      <ElImage
        :src="displayImageUrl"
        :class="`image-single-item-${size}`"
        @error="handleError"
        :zoom-rate="1.2"
        :preview-src-list="previewList"
        preview-teleported
        hide-on-click-modal
        :initial-index="0"
        fit="cover"
        style="width: 100%; height: 100%"
      />
      <div :class="`remove-btn-${size}`" @click.stop="handleRemoveImage">×</div>
    </div>

    <!-- 编辑模式：无图（可上传） -->
    <div v-else-if="showUploader" :class="`image-single-uploader-${size}`">
      <ElUpload
        :action="action.value"
        :data="data.value"
        :show-file-list="false"
        :auto-upload="false"
        :before-upload="beforeImageUpload"
        @change="handleFileChange"
        accept="image/jpeg,image/gif,image/png"
        name="file"
        drag
        :headers="uploadHeaders"
      >
        <div :class="`upload-content-wrapper-${size}`">
          <ElIcon :class="`el-icon--upload-${size}`"><UploadFilled /></ElIcon>
          <div :class="`upload-text-${size}`">{{ size === 'small' ? '拖拽或点击' : '拖拽文件到此或点击上传' }}</div>
        </div>
      </ElUpload>
    </div>
  </div>
</template>

<style lang="less" scoped>
.image-single-container {
  display: inline-block;
  padding: 0;
}

// ==================== normal 尺寸（默认，100px*100px）====================
.image-single-group-normal {
  position: relative;
  width: 100px;
  height: 100px;
  margin: 0;
  user-select: none;
}

.image-single-item-normal {
  width: 100%;
  height: 100%;
  border-radius: 6px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  cursor: pointer;
}

.image-single-item-normal:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-single-group-normal :deep(.el-image) {
  width: 100%;
  height: 100%;
  border-radius: 6px;
}

.image-single-group-normal :deep(.el-image__inner) {
  border-radius: 6px;
  object-fit: cover;
}

.remove-btn-normal {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 24px;
  height: 24px;
  background: #f56c6c;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 10;
}

.image-single-group-normal:hover .remove-btn-normal {
  opacity: 1;
}

.image-single-uploader-normal {
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}

.image-single-uploader-normal :deep(.el-upload) {
  border: 2px dashed #c0c4cc;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  border-radius: 6px;
}

.image-single-uploader-normal :deep(.el-upload:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  color: #409eff;
}

.image-single-uploader-normal :deep(.el-upload-dragger) {
  width: 100% !important;
  height: 100% !important;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.upload-content-wrapper-normal {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.el-icon--upload-normal {
  width: 40px;
  height: 40px;
  margin: 0;
}

.upload-text-normal {
  font-size: 11px;
  margin-top: 4px;
  text-align: center;
  color: #606266;
}

// ==================== small 尺寸（60px*60px）====================
.image-single-group-small {
  position: relative;
  width: 60px;
  height: 60px;
  margin: 0;
  user-select: none;
}

.image-single-item-small {
  width: 100%;
  height: 100%;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
  transition: all 0.3s ease;
  cursor: pointer;
}

.image-single-item-small:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-single-group-small :deep(.el-image) {
  width: 100%;
  height: 100%;
  border-radius: 4px;
}

.image-single-group-small :deep(.el-image__inner) {
  border-radius: 4px;
  object-fit: cover;
}

.remove-btn-small {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  background: #f56c6c;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  font-weight: bold;
  line-height: 1;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 10;
}

.image-single-group-small:hover .remove-btn-small {
  opacity: 1;
}

.image-single-uploader-small {
  width: 60px;
  height: 60px;
  flex-shrink: 0;
  box-sizing: border-box;
}

.image-single-uploader-small :deep(.el-upload) {
  border: 2px dashed #c0c4cc;
  width: 100% !important;
  height: 100% !important;
  margin: 0 !important;
  border-radius: 4px;
  box-sizing: border-box;
}

.image-single-uploader-small :deep(.el-upload:hover) {
  border-color: #409eff;
  background: #f0f7ff;
  color: #409eff;
}

.image-single-uploader-small :deep(.el-upload-dragger) {
  width: 100% !important;
  height: 100% !important;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  box-sizing: border-box;
}

.upload-content-wrapper-small {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  gap: 0;
}

.el-icon--upload-small {
  width: 24px;
  height: 24px;
  margin: 0;
}

.el-icon--upload-small :deep(svg) {
  width: 24px !important;
  height: 24px !important;
}

.upload-text-small {
  font-size: 10px;
  margin-top: 4px;
  text-align: center;
  color: #606266;
  line-height: 1.2;
}
</style>

