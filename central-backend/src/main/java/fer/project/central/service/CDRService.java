package fer.project.central.service;

import fer.project.central.model.CDRRecord;
import fer.project.central.repository.CDRRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class CDRService {

    private final CDRRepository cdrRepository;

    public Page<CDRRecord> getAllRecords(Pageable pageable) {
        return cdrRepository.findAll(pageable);
    }

    public Optional<CDRRecord> getMostRecentByImei(String imei) {
        return cdrRepository.findFirstByImeiOrderByTimestampArrivalDesc(imei);
    }

    public Page<CDRRecord> getByImei(String imei, Pageable pageable) {
        return cdrRepository.findByImei(imei, pageable);
    }

    public Page<CDRRecord> getByBtsId(String btsId, Pageable pageable) {
        return cdrRepository.findByBtsId(btsId, pageable);
    }

    public Page<CDRRecord> getByTimeRange(LocalDateTime start, LocalDateTime end, Pageable pageable) {
        return cdrRepository.findByTimeRange(start, end, pageable);
    }
}
