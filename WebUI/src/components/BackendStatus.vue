<template>
  <div class="flex gap-3 items-center">
    <div
      v-for="backend in backends"
      :key="backend.name"
      class="flex items-center gap-2 px-3 py-1 rounded-lg bg-black bg-opacity-30 border border-white/10"
    >
      <div
        class="w-3 h-3 rounded-full"
        :class="{
          'bg-green-400': backend.status === 'running',
          'bg-orange-400': backend.status === 'notYetStarted' || backend.status === 'stopped',
          'bg-slate-400': backend.status !== 'running' && backend.status !== 'notYetStarted' && backend.status !== 'stopped'
        }"
      ></div>
      <span class="text-lg text-gray-300 font-bold">{{ backend.displayName }}</span>
    </div>    <button
      @click="$emit('manage-backends')"
      class="ml-4 px-4 py-2 rounded-lg bg-blue-800 hover:bg-blue-500 text-white text-lg font-semibold transition-all duration-200 border-2 border-transparent hover:border-blue-300 shadow-md hover:shadow-lg"
      title="Manage Backends"
    >
      Manage Backends
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useBackendServices } from '@/assets/js/store/backendServices'

// Define emits
const emit = defineEmits<{
  'manage-backends': []
}>()

const backendServices = useBackendServices()

// Define backend configurations
const backendConfigs = [
  { name: 'ai-backend', displayName: 'AI Playground Backend' },
  { name: 'openvino-backend', displayName: 'OpenVINO' },
  { name: 'comfyui-backend', displayName: 'ComfyUI' },
]

const backends = computed(() => {
  return backendConfigs.map(config => {
    const serviceInfo = backendServices.info.find(service => service.serviceName === config.name)
    return {
      name: config.name,
      displayName: config.displayName,
      status: serviceInfo?.status || 'unknown'
    }
  })
})
</script>
