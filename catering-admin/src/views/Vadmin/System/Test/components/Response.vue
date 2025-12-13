<script setup lang="tsx">
import { PropType, reactive, watch, ref } from 'vue'
import { Form, FormSchema } from '@/components/Form'
import { useValidator } from '@/hooks/web/useValidator'
import { useForm } from '@/hooks/web/useForm'
import { getKitchenListApi } from '@/api/vadmin/product/kitchen'
import { ImagePlus } from '@/components/ImagePlus'

const { required } = useValidator()

// ImagePlus 组件引用
const imagePlusRef = ref<InstanceType<typeof ImagePlus>>()

const props = defineProps({
  dialogVisible: {
    type: Boolean,
    required: true
  },
  currentRow: {
    type: Object as PropType<any>,
    default: () => null
  },
  dishStatusOptions: {
    type: Array as PropType<Array<{ label: string; value: number }>>,
    default: () => []
  }
})

const formSchema = reactive<FormSchema[]>([
  {
    field: 'name_unique',
    label: '名称',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'name_display',
    label: '显示名称',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'name_english',
    label: '英文名称',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'kitchen_id',
    label: '厨部',
    colProps: {
      span: 12
    },
    component: 'Select',
    componentProps: {
      style: {
        width: '100%'
      },
      multiple: false,
      props: {
        label: 'name_unique',
        value: 'id'
      }
    },
    optionApi: async () => {
      const res = await getKitchenListApi({ is_active: true })
      return res.data
    },
    value: []
  },
  {
    field: 'price',
    label: '基础售价',
    colProps: {
      span: 12
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'order_number',
    label: '排序号',
    colProps: {
      span: 12
    },
    component: 'Input',
    componentProps: {
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'description',
    label: '简介',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 4,
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'description_english',
    label: '英文简介',
    colProps: {
      span: 24
    },
    component: 'Input',
    componentProps: {
      type: 'textarea',
      rows: 4,
      style: {
        width: '100%'
      }
    }
  },
  {
    field: 'status',
    label: '状态',
    colProps: {
      span: 12
    },
    component: 'Select',
    componentProps: {
      style: {
        width: '100%'
      },
      options: props.dishStatusOptions,
      disabled: true
    },
    value: 0
  },
  {
    field: 'dish_images',
    label: '图片',
    colProps: {
      span: 24
    },
    formItemProps: {
      slots: {
        default: (data: any) => {
          if (!data.dish_images) {
            data.dish_images = []
          }
          return (
            <ImagePlus
              ref={imagePlusRef}
              modelValue={data.dish_images}
              onUpdate:modelValue={(val) => {
                data.dish_images = val
              }}
              limit={10}
            />
          )
        }
      }
    }
  }
])

const rules = reactive({
  name_unique: [required()],
  name_display: [required()],
  kitchen_id: [required()]
})

const { formRegister, formMethods } = useForm()
const { setValues, getFormData, getElFormExpose } = formMethods

const submit = async () => {
  const elForm = await getElFormExpose()
  const valid = await elForm?.validate()
  if (valid) {
    const formData = await getFormData()

    // 上传待上传的图片
    if (imagePlusRef.value && typeof imagePlusRef.value.uploadPendingImages === 'function') {
      await imagePlusRef.value.uploadPendingImages()
      // 重新获取表单数据（因为图片数据已更新）
      return await getFormData()
    }

    return formData
  }
}

watch(
  () => props.currentRow,
  (currentRow) => {
    if (!currentRow) return
    setValues(currentRow)
  },
  {
    deep: true,
    immediate: true
  }
)

defineExpose({
  submit
})
</script>

<template>
  <Form
    :rules="rules"
    :validate-on-rule-change="false"
    @register="formRegister"
    :schema="formSchema"
  />
</template>
