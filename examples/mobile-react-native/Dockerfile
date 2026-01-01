# ANALYTICA Mobile React Native
# Build Android APK in Docker

FROM reactnativecommunity/react-native-android:latest AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source
COPY . .

# Build Android release
RUN cd android && ./gradlew assembleRelease

# Output APK
FROM alpine:latest
COPY --from=builder /app/android/app/build/outputs/apk/release/app-release.apk /dist/
CMD ["ls", "-la", "/dist"]
