/**
 * 用户行为上报工具
 */
import request from '@/utils/request'

const debounceTimers = {}

export function trackBehavior(type, id, action, value, debounceMs) {
  if (debounceMs === undefined) debounceMs = 0

  const debounceKey = type + '-' + id + '-' + action

  if (debounceTimers[debounceKey]) {
    clearTimeout(debounceTimers[debounceKey])
  }

  const doTrack = function() {
    return new Promise(function(resolve, reject) {
      const url = '/user/profile/behavior/' + type + '/' + id + '/' + action
      const params = {}

      if (value !== undefined) {
        params.behavior_value = value
      }

      request.get(url, { params: params })
        .then(function() {
          delete debounceTimers[debounceKey]
          resolve()
        })
        .catch(function(error) {
          console.warn('[行为上报] 失败:', error)
          resolve()
        })
    })
  }

  if (debounceMs > 0) {
    return new Promise(function(resolve) {
      const timer = setTimeout(function() {
        doTrack().then(resolve)
      }, debounceMs)
      debounceTimers[debounceKey] = timer
    })
  }

  return doTrack()
}

export function trackCourseView(courseId, duration) {
  return trackBehavior('course', courseId, 'view', duration, 1000)
}

export function trackCourseCollect(courseId) {
  return trackBehavior('course', courseId, 'collect')
}

export function trackCourseRate(courseId, rating) {
  return trackBehavior('course', courseId, 'rate', rating)
}

export function trackCourseComplete(courseId) {
  return trackBehavior('course', courseId, 'complete')
}

export function trackKnowledgeView(pointId, duration) {
  return trackBehavior('knowledge', pointId, 'view', duration, 1000)
}

export function trackKnowledgeComplete(pointId) {
  return trackBehavior('knowledge', pointId, 'complete')
}

export function trackResourceView(resourceId, progress) {
  return trackBehavior('resource', resourceId, 'view', progress, 2000)
}

export function trackResourceComplete(resourceId) {
  return trackBehavior('resource', resourceId, 'complete')
}