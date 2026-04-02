import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';

const Antigravity = ({
    count = 350,
    magnetRadius = 8,
    ringRadius = 10,
    waveSpeed = 0.4,
    waveAmplitude = 1,
    particleSize = 1.2,
    lerpSpeed = 0.08,
    color = '#8ea7ff',
    autoAnimate = true,
    particleVariance = 1,
    rotationSpeed = 0.02,
    depthFactor = 1,
    pulseSpeed = 2,
    particleShape = 'capsule'
}) => {
    const containerRef = useRef(null);

    useEffect(() => {
        if (!containerRef.current) return;

        // --- SETUP ---
        const width = containerRef.current.clientWidth;
        const height = containerRef.current.clientHeight;

        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(35, width / height, 0.1, 1000);
        camera.position.z = 50;

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        containerRef.current.appendChild(renderer.domElement);

        // --- GEOMETRY ---
        let geometry;
        if (particleShape === 'capsule') geometry = new THREE.CapsuleGeometry(0.1, 0.4, 4, 8);
        else if (particleShape === 'sphere') geometry = new THREE.SphereGeometry(0.2, 16, 16);
        else if (particleShape === 'box') geometry = new THREE.BoxGeometry(0.3, 0.3, 0.3);
        else geometry = new THREE.TetrahedronGeometry(0.3);

        const material = new THREE.MeshBasicMaterial({ color: new THREE.Color(color) });
        const iMesh = new THREE.InstancedMesh(geometry, material, count);
        scene.add(iMesh);

        // --- PARTICLES DATA ---
        const particles = [];
        const dummy = new THREE.Object3D();

        // Approximate viewport size at z=0
        const vHeight = 2 * Math.tan((camera.fov * Math.PI) / 360) * camera.position.z;
        const vWidth = vHeight * camera.aspect;

        for (let i = 0; i < count; i++) {
            const x = (Math.random() - 0.5) * vWidth * 1.5;
            const y = (Math.random() - 0.5) * vHeight * 1.5;
            const z = (Math.random() - 0.5) * 20;

            particles.push({
                t: Math.random() * 100,
                speed: 0.01 + Math.random() / 150,
                mx: x, my: y, mz: z,
                cx: x, cy: y, cz: z,
                randomRadiusOffset: (Math.random() - 0.5) * 2
            });
        }

        // --- INTERACTION ---
        const mouse = new THREE.Vector2(-1000, -1000);
        const virtualMouse = new THREE.Vector2(0, 0);
        let lastMouseMoveTime = 0;

        const onMouseMove = (e) => {
            const rect = containerRef.current.getBoundingClientRect();
            mouse.x = ((e.clientX - rect.left) / width) * 2 - 1;
            mouse.y = -((e.clientY - rect.top) / height) * 2 + 1;
            lastMouseMoveTime = Date.now();
        };

        window.addEventListener('mousemove', onMouseMove);

        // --- ANIMATION LOOP ---
        let animationFrameId;
        const clock = new THREE.Clock();

        const animate = () => {
            const time = clock.getElapsedTime();

            // Handle Mouse smoothing
            let targetX = (mouse.x * vWidth) / 2;
            let targetY = (mouse.y * vHeight) / 2;

            if (autoAnimate && Date.now() - lastMouseMoveTime > 2000) {
                targetX = Math.sin(time * 0.5) * (vWidth / 6);
                targetY = Math.cos(time * 0.5 * 2) * (vHeight / 6);
            }

            virtualMouse.x += (targetX - virtualMouse.x) * 0.05;
            virtualMouse.y += (targetY - virtualMouse.y) * 0.05;

            const globalRotation = time * rotationSpeed;

            for (let i = 0; i < count; i++) {
                const p = particles[i];
                p.t += p.speed;

                const projectionFactor = 1 - p.cz / 50;
                const projTargetX = virtualMouse.x * projectionFactor;
                const projTargetY = virtualMouse.y * projectionFactor;

                const dx = p.mx - projTargetX;
                const dy = p.my - projTargetY;
                const dist = Math.sqrt(dx * dx + dy * dy);

                let tx = p.mx;
                let ty = p.my;
                let tz = p.mz * depthFactor;

                if (dist < magnetRadius) {
                    const angle = Math.atan2(dy, dx) + globalRotation;
                    const wave = Math.sin(p.t * waveSpeed + angle) * (0.5 * waveAmplitude);
                    const currentRingRadius = ringRadius + wave + p.randomRadiusOffset;

                    tx = projTargetX + currentRingRadius * Math.cos(angle);
                    ty = projTargetY + currentRingRadius * Math.sin(angle);
                    tz = p.mz * depthFactor + Math.sin(p.t) * (1 * waveAmplitude * depthFactor);
                }

                p.cx += (tx - p.cx) * lerpSpeed;
                p.cy += (ty - p.cy) * lerpSpeed;
                p.cz += (tz - p.cz) * lerpSpeed;

                dummy.position.set(p.cx, p.cy, p.cz);
                dummy.lookAt(projTargetX, projTargetY, p.cz);
                dummy.rotateX(Math.PI / 2);

                const curDist = Math.sqrt(Math.pow(p.cx - projTargetX, 2) + Math.pow(p.cy - projTargetY, 2));
                const distFromRing = Math.abs(curDist - ringRadius);
                let scale = Math.max(0, Math.min(1, 1 - distFromRing / 10));
                scale = scale * (0.8 + Math.sin(p.t * pulseSpeed) * 0.2 * particleVariance) * particleSize;

                dummy.scale.set(scale, scale, scale);
                dummy.updateMatrix();
                iMesh.setMatrixAt(i, dummy.matrix);
            }

            iMesh.instanceMatrix.needsUpdate = true;
            renderer.render(scene, camera);
            animationFrameId = requestAnimationFrame(animate);
        };

        animate();

        // --- CLEANUP ---
        const handleResize = () => {
            if (!containerRef.current) return;
            const w = containerRef.current.clientWidth;
            const h = containerRef.current.clientHeight;
            renderer.setSize(w, h);
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('mousemove', onMouseMove);
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            if (containerRef.current && renderer.domElement) {
                containerRef.current.removeChild(renderer.domElement);
            }
            renderer.dispose();
            geometry.dispose();
            material.dispose();
        };
    }, [count, magnetRadius, ringRadius, waveSpeed, waveAmplitude, particleSize, lerpSpeed, color, autoAnimate, particleVariance, rotationSpeed, depthFactor, pulseSpeed, particleShape]);

    return <div ref={containerRef} style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }} />;
};

export default Antigravity;
