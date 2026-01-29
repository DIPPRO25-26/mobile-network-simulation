package fer.project.central.service;

import fer.project.central.exception.BtsNotFoundException;
import fer.project.central.exception.DuplicateBtsException;
import fer.project.central.model.BTS;
import fer.project.central.repository.BTSRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class BTSService {

    private final BTSRepository btsRepository;

    public List<BTS> getAllBTS() {
        return btsRepository.findAll();
    }

    public BTS getBTSByBtsId(String btsId) {
        return btsRepository.findByBtsId(btsId)
                .orElseThrow(() -> new BtsNotFoundException(btsId));
    }

    public BTS registerBTS(BTS bts) {
        // ✅ business validation (polja postoje, ali provjeri da imaju smisla)
        validateBtsBusinessRules(bts);

        if (btsRepository.findByBtsId(bts.getBtsId()).isPresent()) {
            throw new DuplicateBtsException(bts.getBtsId());
        }

        bts.setCreatedAt(LocalDateTime.now());
        bts.setUpdatedAt(LocalDateTime.now());

        return btsRepository.save(bts);
    }

    public BTS updateBTSStatus(String btsId, String newStatus) {
        BTS bts = getBTSByBtsId(btsId);

        // minimalna normalizacija (da " ACTIVE " ne radi probleme)
        String normalized = newStatus == null ? null : newStatus.trim();

        if (normalized == null || normalized.isEmpty()) {
            throw new IllegalArgumentException("status must not be empty");
        }

        if (!bts.getStatus().equals(normalized)) {
            bts.setStatus(normalized);
            bts.setUpdatedAt(LocalDateTime.now());
            return btsRepository.save(bts);
        }

        return bts;
    }

    /**
     * Minimalna provjera smislenosti vrijednosti (ne zamjenjuje @Valid anotacije).
     * Ova pravila su "safe" i neće ti razbiti flow:
     * - maxCapacity > 0
     * - currentLoad u [0, maxCapacity]
     */
    private void validateBtsBusinessRules(BTS bts) {
        if (bts == null) {
            throw new IllegalArgumentException("BTS payload is required");
        }

        // ako su ovi fieldovi primitive int u BTS modelu, null check nije potreban,
        // ali je bezopasan ako su Integer.
        Integer maxCapacity = bts.getMaxCapacity();
        Integer currentLoad = bts.getCurrentLoad();

        if (maxCapacity == null || maxCapacity <= 0) {
            throw new IllegalArgumentException("maxCapacity must be > 0");
        }

        if (currentLoad == null || currentLoad < 0) {
            throw new IllegalArgumentException("currentLoad must be >= 0");
        }

        if (currentLoad > maxCapacity) {
            throw new IllegalArgumentException("currentLoad must be <= maxCapacity");
        }
    }
}
